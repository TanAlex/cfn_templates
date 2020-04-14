import glob
import sys
import os
import sqlite3 as sqlite
# https://gist.githubusercontent.com/pfdevmuller/4085480/raw/4645854b2d962afda0060f7ed0450afd13527b2a/RunDatabaseScripts.py

def LoadScripts(scriptFolder):
    ''' Returns a list of module references '''
    # Find Script Files:
    scriptFiles = glob.glob(os.path.join(scriptFolder, "Script*.py"))
    print "Found %d Script Files" % (len(scriptFiles))
    
    # Load scripts:
    loadedScripts = []
    for scriptFile in scriptFiles:
        try:
        
            # Get full module name:
            scriptName = os.path.basename(scriptFile)
            scriptName = os.path.splitext(scriptName)[0]    
            folderName = os.path.basename(scriptFolder)
            fullModuleName = "%s.%s" % (folderName, scriptName)
        
            # Import Script:
            script_module = __import__(fullModuleName, fromlist=["fullModuleName"])
        
            # Store reference to Script:
            loadedScripts.append(script_module)
            
        except Exception, e:
            print "Something went wrong while loading script file \'%s\'" % scriptFile
            print e
    
    return loadedScripts
                
def RunScripts(databaseFilename, loadedScripts):
    try:       
        # Open DB:
        connection = sqlite.connect(databaseFilename)
        
        # Keep a list of completed scripts so scripts can test if they are ready to run:
        namesOfCompletedScripts = []
        success = True
        # Keep passing over list until everything has been run:
        while (len(namesOfCompletedScripts) < len(loadedScripts)):
            nothingExecutedOnThisPass = True
            # Iterate over scripts:
            for script in loadedScripts:
                try:
                    # Check if this script has been run or not:
                    if (script.Name not in namesOfCompletedScripts):
                        # Ask script if it is ready to run -
                        # - give it a list of completed scripts:
                        if (script.CanRun(connection, namesOfCompletedScripts)):
                            # Run script:
                            script.Run(connection)
                            namesOfCompletedScripts.append(script.Name)                                  
                            nothingExecutedOnThisPass = False
                        else:
                            print "\n%s not ready to run" % script.Name
            
                except Exception, e:
                    print "Something went wrong while running script %s" % script.Name
                    print e
                    success = False
                    
            if (nothingExecutedOnThisPass):
                # If nothing executed on this pass, we're stuck -
                # - the remaining scripts won't run
                break
        
        print "\nThe following scripts were successfully run:"
        print namesOfCompletedScripts
        
        if (len(namesOfCompletedScripts) < len(loadedScripts)):
            print "Some scripts failed:"
            for script in loadedScripts:
                if (script.Name not in namesOfCompletedScripts):
                    print "\t" + script.Name
           
    except Exception, e:
        print "Something went wrong while applying scripts to DB"
        print e
    finally:
        # Close DB:
        connection.close()

if __name__ == "__main__":
    if (len(sys.argv) != 3):
        print "\n\tRequires two arguments:"        
        print "\n\t\tRunDatabaseScripts.py {databasefilename} {scriptfolder}\n\n"
        sys.exit()
    
    databaseFilename = sys.argv[1]
    scriptFolder = sys.argv[2]
        
    # Load Scripts:
    loadedScripts = LoadScripts(scriptFolder)
    RunScripts(databaseFilename, loadedScripts)
    
    