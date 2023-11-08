# lumina-binja
IDA's [Lumina](https://hex-rays.com/products/ida/lumina/) feature, reimplemented for Binary Ninja. This fork adds a few main things:
- Error handling
- Instructions on how to use
- It doesn't overwrite user/signature-defined functions
- Removal of a non-working feature

## But what are all of the commits?
I edited the readme... a lot.

## Setup
1. Please use Linux.
2. Clone this repo into your $HOME/.binaryninja/plugins folder.
3. cd to the cloned folder.
4. Run `/usr/bin/python3.11 -m pip --isolated --disable-pip-version-check install --upgrade --upgrade-strategy only-if-needed --target $HOME/.binaryninja/python311/site-packages -r requirements.txt` (Note that this command might not work on your computer; consider using just "python," ensuring pip is installed, or replacing $home with your actual home).
5. Also run `/usr/bin/python3.11 -m pip --isolated --disable-pip-version-check install --upgrade --upgrade-strategy only-if-needed --target $HOME/.binaryninja/python311/site-packages construct`
6. Now it *should* be able to launch. If it can't, please open an issue.
7. Launch Binary Ninja.
8. Go to settings.
9. Search for "lumina."
10. You can configure it if you have an IDA license. If you don't, keep reading.
11. In the host field, enter "lumen.abda.nl," and set the port to 1235. Download [this cert](https://abda.nl/lumen/hexrays.crt), and enter the path to it (like /home/h/Downloads/hexrays.crt) under "lumina cert." (Note: There are not many people who use Lumen, here's a small list of people who do: people who use cracked versions of IDA, people who have expired IDA licenses, and people like you who use plugins like these!)
12. Relaunch Binary Ninja.
13. Open a binary.
14. Go to plugins, Lumina, pull all metadata, and it should do something!

## Additional info
 - If you want to override ALL functions (not the default, which is only overriding things that start with sub_) go to parsing.py at line 120 and follow the instructions given.
 - Tested on binary ninja 3.5-stable & 3.6-dev
 - Tested with python 3.11
 - Compatible with existing public Lumina databases (both official[^1] and unofficial), including TLS support
 - Signatures largely match IDA's implementation, enabling cross-disassembler collaboration (~85% accuracy, including discrepancies in analysis between disassemblers)
 - Supported Architectures:
   - [x] x86 / x86_64
 - Supported metadata types:
   - [x] function names
   - [x] comments
     - [x] instruction level comments
     - [x] function level comments
   - [x] function type info (currently parsing only)
     - [x] calling conventions
       - [x] generic conventions
     - [x] return type
     - [x] parameter types
     - [x] stack frame info
       - [x] variable names
       - [x] variable offsets and sizes
       - [x] variable types
 - All type info is supported, except structs and enums due to limitations of the current Lumina specification

## Security notice
Please note that this uses SSL/TLS protocol version TLSv1, and it's not secure or something idrk. If anyone is mitming your network, don't use this.

## Credits
 - [Lumen](https://github.com/naim94a/lumen) for most of the RPC protocol reversing
 - [Synactiv's blog](https://www.synacktiv.com/en/publications/investigating-ida-lumina-feature.html) for a high-level overview of how Lumina works
 - [Me](https://twitter.com/0x62797465) for fixing stuff

**Maple Bacon maintainers:**
 - [@nneonneo](https://github.com/nneonneo) for metadata reversing and implementation
 - [@desp](https://github.com/despawningbone) for signature generation and tinfo reversing, and stitching everything together

[^1]: Provided that you have specified a valid IDA license file as the key file in the settings, along with the valid certificate to connect to `lumina.hex-rays.com`.
