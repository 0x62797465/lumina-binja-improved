from binaryninja import BinaryView, Function, BackgroundTask, Type
from binaryninja.transform import Transform
from binaryninja.log import log_debug
from binaryninja.log import Logger
from binaryninja import demangle_ms, demangle_gnu3, get_qualified_name
import socket, itertools
from construct import *
from lumina_structs import *
from lumina_structs.metadata import *
    
from .sig.util import Sig, ARCH_MAPPING
from .type import construct_type
log = Logger(0, 'LuminaParse')
#
# Push Functions
#

def extract_md(bv: BinaryView, func: Function, gen: Sig) -> dict:
    chunks = []

    #apply comments; theres no anterior/posterior/repeatable comments in binja - use MD_INSN_CMT is enough
    if func.comment:
        chunks.append({
            'type': MetadataType.MD_FUNC_CMT,
            'data': {'text': func.comment}})
            #TODO see if need unparsed
    
    if func.comments:
        chunks.append({
            'type': MetadataType.MD_INSN_CMT,
            'data': [{
                'offset': addr - func.start,
                'text': cmt} 
                for addr, cmt in func.comments.items()]})

    #TODO frame info and tinfo
    #OPREPRS as a concept doesnt really exist in binja afaik (coz all of the potential references are offsets regardless),
    #but might be helpful in defining data vars so parsing might be good

    if chunks: #only compute signature and returns something if has data
        sig, block, mask = gen.calc_func_metadata(func)

        return {
            "metadata": {
                "func_name": func.name,  #func name is automatically whatever it should be
                "func_size": len(block),
                "serialized_data": {
                    "chunks": chunks}},
            "signature": {
                "version": 1, 
                "signature": sig}}
    else:
        return None



def craft_push_md(bv: BinaryView, funcs: list[Function], task: BackgroundTask = None) -> dict:
    if task:
        task.progress = '[Lumina] Calculating binary checksum'

    with open(bv.file.original_filename, 'rb') as f:  #file mightve been patched in between pushes, so reread
        buf = f.read()

    progress = "[Lumina] Extracting function metadata ({count}/" + str(len(funcs)) + " functions)"
    push, eas = [], []
    for i, f in enumerate(funcs):
        md = extract_md(bv, f, ARCH_MAPPING[f.arch.name](bv))
        if md: #only apply if extracted useful data
            push.append(md)
            eas.append(f.start)
        if task:
            task.progress = progress.format(count=i)

    return {
        "type": PushMdOpt.PUSH_OVERRIDE_IF_BETTER,  #protocol 2 default
        "idb_filepath": bv.file.filename, 
        "input_filepath": bv.file.original_filename, 
        "input_md5": Transform['MD5'].encode(buf),
        "hostname": socket.gethostname(),
        "funcInfos": push,
        "funcEas": eas}  #seems like ida is offset by one???


#
# Pull Functions
#


#can return multiple queries coz binja supports multiple archs in one binary view unlike IDA
def craft_pull_md(bv: BinaryView, funcs: list[Function], task: BackgroundTask = None) -> list[dict]:
    #groupby needs the list to be sorted first
    k = lambda f: f.arch.name #sort and group according to arch
    groups = [[f for f in g[1]] for g in itertools.groupby(sorted(funcs, key=k), key=k)]

    mds = []

    for fs in groups:
        sigs = []
        i = 0
        progress = "[Lumina] Calculating function signatures ({count}/" + str(len(funcs)) + " functions)"
        for func in fs:
            #arch can change between funcs
            if task:
                task.progress = progress.format(count=i)
            sigs.append({'signature':ARCH_MAPPING[func.arch.name](bv).calc_func_metadata(func)[0]})
            i+=1

        mds.append({'flags': 1,  #protocol 2 default
            'types':[],
            'funcInfos':sigs})

    return mds



def apply_md(bv: BinaryView, func: Function, info: Container):
    #we don't really care about popularity atm, but it might be useful server side for sorting
    # Assuming you have a function named 'func'
    # If you want to overwide everything, comment eveything starting here and...
    text_to_find = "sub_" # if it works it works
    if text_to_find in str(func):                                       # a few more line
        ()
    else:
        return                                                          # and here, this is the last line you have to comment

    #IDA (at least on 7.5) hardcoded no-override flag into apply_metadata, so tinfo and frame desc effectively never gets applied even if existing data is entirely auto-generated
    #we won't follow that - manually clearing the data on every lumina pull is very annoying and there is undo anyway
    #instead we will default to resetting metadata to what lumina provides on conflict // BOBERTTT commenting, yeah no f this
    ms = demangle_ms(bv.arch, info.metadata.func_name)
    gnu = demangle_gnu3(bv.arch, info.metadata.func_name)

    if ms[0] != None:
        a = get_qualified_name(ms[1])
    elif gnu[0] != None:
        a = get_qualified_name(gnu[1])
    else:
        a = info.metadata.func_name
    func.name = a
    #func size should be the same to be able to get the same signature, so no need to set
    for md in info.metadata.serialized_data.chunks:
        if md.type in [MetadataType.MD_INSN_CMT, MetadataType.MD_INSN_REPCMT]:
            for c in md.data:
                addr = func.start + c.offset
                func.set_comment_at(addr, c.text)
        elif md.type in [MetadataType.MD_FUNC_CMT, MetadataType.MD_FUNC_REPCMT]:
            func.comment = md.data.text
        elif md.type == MetadataType.MD_EXTRA_CMT:
            #TODO figure out how to use wrap_comment and see if it enables actual anterior/posterior comments
            for c in md.data:
                addr = func.start + c.offset
                #only | if is not empty string
                func.set_comment_at(addr, ' | '.join(filter(bool, [c.anterior, (cmt if (cmt:=func.get_comment_at(addr)) else ''), c.posterior])))
        elif md.type == MetadataType.MD_TYPE_INFO:
            try:
                t = construct_type(bv, md.data.tinfo, md.data.names)
            except:
                ()
            #TODO handle argloc with set_call_reg_*(?)
            try:
                func.function_type = t
            except:
                ()
        elif md.type == MetadataType.MD_FRAME_DESC:
            #binja doesnt have the variable definition section for comments storage, so discard for now; also repr as a concept doesnt exist in binja
            for var in md.data.vars:
                #sometimes type == None if its default so just treat it as byte array of nbytes
                try:
                    t = construct_type(bv, var.type.tinfo, var.type.names, var.nbytes) if var.type else Type.array(Type.int(1, sign=False, alternate_name='byte'), var.nbytes)
                    name = var.name if var.name else f'lumina_{hex(var.off)}'

                except:
                    ()
                #TODO check if this still matches in architectures with stack growing up
                func.delete_auto_stack_var(-(md.data.frsize - var.off + md.data.frregs))  #binja uses rbp instead of rsp (offset goes down instead of up)
                func.create_user_stack_var(-(md.data.frsize - var.off + md.data.frregs), t, name)  #auto var gets overwritten by reanalysis
            func.reanalyze()
        else:
            #logger is likely already instantiated by client.py, we can just invoke it with the name now
            log_debug('Unimplemented metadata type ' + str(md.type) + ', skipping for now...', logger='Lumina')
