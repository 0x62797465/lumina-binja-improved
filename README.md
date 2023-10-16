# lumina-binja
IDA's [Lumina](https://hex-rays.com/products/ida/lumina/) feature, reimplemented for Binary Ninja

Please note that this uses SSL/TLS protocol version TLSv1, and it's not secure or something idrk. If anyone is mitming your network maybe don't use this I guess.

## Setup
1. Please use Linux.
2. Clone this repo into your $home/.binaryninja/plugins folder.
3. cd to the cloned folder.
4. Run `/usr/bin/python3.11 -m pip --isolated --disable-pip-version-check install --upgrade --upgrade-strategy only-if-needed --target $home/.binaryninja/python311/site-packages -r requirements.txt` (Note that this command might not work on your computer; consider using just "python," ensuring pip is installed, or replacing $home with your actual home).
5. Now it *should* be able to launch. If it can't, please open an issue.
6. Launch Binary Ninja.
7. Go to settings.
8. Search for "lumina."
9. You can configure it if you have an IDA license. If you don't, keep reading.
10. In the host field, enter "lumen.abda.nl," and set the port to 1235. Download [this cert](https://abda.nl/lumen/hexrays.crt), and enter the path to it (like /home/h/Downloads/hexrays.crt) under "lumina cert."
11. Relaunch Binary Ninja.
12. Open a binary.
13. Go to plugins, Lumina, pull all metadata, and it should do something!

## Demo
(In this poor quality gif I am using a shortcut to pull metadata for a stripped golang binary)
![2023-10-16 08-04-09](https://github.com/Boberttt/lumina-binja-improved/assets/104478197/e7880ac6-5240-43a4-9d41-e568b1059982)

## How is the fork different?
- It's maintained (to an extent)
- It doesn't overwrite existing functions
- It doesn't throw errors (as much)
- It fixes a requirement bug (which I think only happens on windows??? idrk)
- It has installation and usage instructions
- The readme is improved

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

## Credits
 - [Lumen](https://github.com/naim94a/lumen) for most of the RPC protocol reversing
 - [Synactiv's blog](https://www.synacktiv.com/en/publications/investigating-ida-lumina-feature.html) for a high-level overview of how Lumina works
 - [Me](https://twitter.com/0x62797465) for fixing stuff

**Maple Bacon maintainers:**
 - [@nneonneo](https://github.com/nneonneo) for metadata reversing and implementation
 - [@desp](https://github.com/despawningbone) for signature generation and tinfo reversing, and stitching everything together

[^1]: Provided that you have specified a valid IDA license file as the key file in the settings, along with the valid certificate to connect to `lumina.hex-rays.com`.
