from binaryninja import *
from binaryninja.log import Logger

from lumina_structs import *

import socket, ssl

from .sig.util import ARCH_MAPPING
from .parsing import apply_md, craft_push_md, craft_pull_md

log = Logger(0, 'Lumina')


class LuminaClient:
    def __init__(self) -> None:
        self.socket = None
        self.lock = threading.RLock() #we need RLock to be able to enter critical sections holding a lock already
        self.reconnect()

    def is_valid(self, bv: BinaryView, func: Function = None):
        return self.socket and (func.arch.name in ARCH_MAPPING if func else True)
    
    def send_and_recv_rpc(self, code: RPC_TYPE, noretry: bool = False, **kwargs):
        try: 
            with self.lock: #only lock if not already in critical section (see reconnect())
                payload = rpc_message_build(code, **kwargs)
                log.log_debug('Sending ' + str(code) + ' command (' + str(payload) + ')')
                self.socket.send(payload)

                packet, message = rpc_message_parse(self.socket)
                log.log_debug('Received ' + str(packet) + 'Message: ' + str(message) + '')
                return packet, message
        except (ConnectionError, con.StreamError):
            log.log_warn('Disconnected from the Lumina server.' + ('' if noretry else ' Reconnecting...'))
            if not noretry:
                self.reconnect()
                return self.send_and_recv_rpc(code, **kwargs)  #retry
            return (None, None)
        except Exception as e:
            log.log_error('Something went wrong: ' + str(type(e)) + ': ' + str(e))
            return (None, None)


    def reconnect(self, *_):  #ignore additional args
        s = Settings()
        with self.lock:  #lock until handshakes over to avoid other reqs go faster than we do
            try:
                if self.socket:  #reset connection
                    self.socket.close()

                host = s.get_string('lumina.host'), int(s.get_string('lumina.port'))

                self.socket = socket.socket()
                self.socket.connect(host)

                cert = s.get_string('lumina.cert')
                if cert:
                    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
                    context.load_verify_locations(cert)
                    self.socket = context.wrap_socket(self.socket, server_hostname=host[0])

                key, id = b'', bytes(6)
                try:
                    keypath = s.get_string('lumina.key')
                    if keypath:
                        with open(keypath, 'rb') as kf:
                            key = kf.read()
                            if key.startswith(b'HEXRAYS_LICENSE'):    #looks like genuine license, parse id
                                #id is from the line with IDAPRO*W in it
                                id = bytes.fromhex(key.split(b' IDAPRO')[0].split(b'\n')[-1].replace(b'-', b'').decode())
                                if len(id) != 6:   #must be 6 bytes long, if not something went wrong
                                    id = bytes(6)  #reset into empty bytes
                                    raise ValueError()
                except OSError:
                    log.log_warn('Lumina key file path is invalid, ignoring...')
                except ValueError:
                    log.log_warn('Given Hexrays license file seems malformed, skipping parsing...')

                resp, msg = self.send_and_recv_rpc(RPC_TYPE.RPC_HELO, noretry=True, protocol=2, hexrays_license=key, hexrays_id=id, field_0x36=0)
                if not resp or resp.code != RPC_TYPE.RPC_OK:
                    raise ConnectionError('Handshake failed ' + (f'({msg.message})' if resp and resp.code == RPC_TYPE.RPC_FAIL else '(connection failure)'))

                log.log_info('Connection to Lumina server ' +  host[0] + ':' + str(host[1]) + ' (TLS: ' + str(bool(cert)) + ') succeeded.')
            except Exception as e:
                if self.socket:  #if we got an error after opening the socket, close it; also needs to be locked
                    self.socket.close()
                self.socket = None

                log.log_alert('Connection to Lumina server failed (' + (str(e) if type(e) != ValueError else 'invalid port') + '). Please check your configuration.')

    
    #
    # All functions commands
    #

    def pull_all_mds(self, bv: BinaryView):
        log.log_info("Pulling all function metadata in the background...")

        copy = list(bv.functions)  #just in case functions changed while we were waiting, make a copy since we rely on ordering heavily
        send_and_recv_rpc = self.send_and_recv_rpc

        class RunPull(BackgroundTaskThread):
            def run(self):
                #TODO figure out if using bv has race conditions
                for kwargs in craft_pull_md(bv, copy, self):
                    self.progress = '[Lumina] Sending pull request...'

                    msg = send_and_recv_rpc(RPC_TYPE.PULL_MD, **kwargs)[1]

                    self.progress = '[Lumina] Applying metadata...'

                    if msg:
                        it = iter(msg.results) #also results only have valid mds so its easier to model with iterator
                        for i, found in enumerate(msg.found):
                            if found == ResultType.RES_OK:
                                apply_md(bv, copy[i], next(it))
                        log.log_info('Pulled ' + str(sum([d == ResultType.RES_OK for d in msg.found])) + '/' + str(len(msg.found)) + ' functions successfully.')

        RunPull('[Lumina] Pulling metadata...', True).start()  #doesnt matter if we copy or not here


    #TODO test if we can get worker_enqueue working so we can calc metadata on a thread each
    #so that pulling all metadata wont be this slow for big binaries somehow
    #just calling worker_enqueue(lambda: self.push_function_md(bv, f)) introduces race conditions on f

    #
    # Function specific commands
    #

    def pull_function_md(self, bv: BinaryView, func: Function):
        log.log_debug('Pulling metadata for func ' + func.name + '...')

        #TODO pop up saying "pulling function metadata..."?
        msg = self.send_and_recv_rpc(RPC_TYPE.PULL_MD, **(craft_pull_md(bv, [func])[0]))[1]

        if msg and msg.results:
            apply_md(bv, func, msg.results[0])
            log.log_info('Pulled metadata for function "' + func.name + '" successfully.')
