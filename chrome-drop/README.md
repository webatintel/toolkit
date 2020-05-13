# Provision
## Get all the code
* Copy the related .zip file from server, and unzip it to directory <chromium_webgl>.
* open "cmd"
* set PATH=<chromium_webgl>/depot_tools;%PATH% # Get all necessary tools, including python, git, etc.

## Install Visual Studio (If you want to build Chromium)
As of September, 2017 (R503915) Chromium requires Visual Studio 2017 (15.7.2) to build. The clang-cl compiler is used but Visual Studio's header files, libraries, and some tools are required. Visual Studio Community Edition should work. You must install the “Desktop development with C++” component and the “MFC and ATL support” sub-component.
You must have the version 10.0.17134 Windows 10 SDK installed. This can be installed separately or by checking the appropriate box in the Visual Studio Installer.
The SDK Debugging Tools must also be installed. If the Windows 10 SDK was installed via the Visual Studio installer, then they can be installed by going to: Control Panel → Programs → Programs and Features → Select the "Windows Software Development Kit" → Change → Change → Check “Debugging Tools For Windows” → Change. Or, you can download the standalone SDK installer and use it to install the Debugging Tools.

# Sync latest code
* cd <toolkit> && git pull
* cd <chromium_webgl>/test
* python webgl.py --daily
