# launcher/gateway-launcher.py
#
# Copyright (C) 2013-2014 Long Range Systems, LLC., All rights reserved.

LAUNCHER_VERSION = '1.1'
LAUNCHER_SVNVERSION = filter(str.isdigit, '$Rev: 63729 $')

def usage(exit=True):
    print("Usage: gateway-launcher.py " +
          "<app.zip> <start module> <start function>")
    if usage:
        sys.exit(1)

if __name__ == '__main__':
    import importlib
    import os
    import shutil
    import sys
    from zipfile import ZipFile

    script_fn = os.path.abspath(__file__)
    script_dir = os.path.dirname(script_fn)

    # If we are being run from a zipfile, we don't need the zip file passed
    # on the command line.
    # NOTE: You can not include the compiled .pyc launcher in your zip
    # or this zip detection will not work!
    if script_dir.endswith('.zip'):
        zip_path = script_dir
    else:
        # Add zipfile path user passed to sys.path
        try:
            zip_path = sys.argv[1]    # name of zipfile with application
        except:
            usage()
        sys.path.append(zip_path)
    zip_fn = os.path.basename(zip_path)


    # zipimporter doesn't work with dynamic libraries (*.so and *.pyd).
    # We will manually extract dynamic libraries to a temp directory and
    # add the temp directory to sys.path.  We do the extract to the temp
    # directory because this is tmpsfs RAM disk on the cpx2e and will thus
    # be clean on every boot.  This way, if we extract a bogus dynamic library,
    # simply rebooting will clear it out for us.
    solib_tmpdir = os.path.join('/tmp', zip_fn + '.solib')
    if os.path.exists(solib_tmpdir):
        if os.path.isdir(solib_tmpdir):
            shutil.rmtree(solib_tmpdir)
        else:
            os.remove(solib_tmpdir)
    os.mkdir(solib_tmpdir)
    sys.path.append(solib_tmpdir)
    lm_py = None
    with ZipFile(zip_path) as zipfile:
        for fname in zipfile.namelist():
            if fname.endswith('.so') or fname.endswith('.pyd'):
                zipfile.extract(fname, solib_tmpdir)
            elif fname.endswith("launcher-main.py"):
                lm_py = fname

    # If we found a launcher-main.py, then import that and assume that'll
    # it'll just start running the application.
    if lm_py is not None:
        start_module_name = os.path.splitext(lm_py)[0].replace('/', '.')
        start_function_name = 'launcherStart'
    else:
        # No launcher-main.py, need to be told what to load and start
        try:
            start_module_name = sys.argv[2] # name of module with start function
            start_function_name = sys.argv[3] # name of start function
        except:
            usage()

    start_module = importlib.import_module(start_module_name)
    if start_function_name is not None:
        getattr(start_module, start_function_name)()
