[app]

# (str) Title of your application
title = Apex Trader Pro

# (str) Package name
package.name = apextraderpro

# (str) Package domain (needed for android packaging)
package.domain = org.apextrader

# (list) Source files to include (let it empty to include all the files)
source.include_exts = py,png

# (list) Directory to load source from
source.dir = .

# (str) Application versioning
version = 1.0

# (list) Application requirements
# Limitado estrictamente para evitar sobrecarga de memoria
requirements = python3,kivy,requests

# (str) Supported orientations
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET

# (int) Target Android API, should be as high as possible.
android.api = 33

# (int) Minimum API your APK will support.
android.minAPI = 21

# (int) Android SDK version to use
android.sdk = 33

# (str) Android build tools version to use
android.build_tools_version = 33.0.0


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (withcommand output))
log_level = 1

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
