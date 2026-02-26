
Thank you for using my app! Currently its very basic, but this is my first attempt at creating a usable, helpful app!
I will constantly be updating it, so watch the github repo.

Currently my app only runs on windows 10. Maybe in the future I can add IOS support or linux support.

HOW TO LAUNCH APP
If you clone the repository, you can launch the app this way:
- Download python
- Download all required libraries from requirements.txt
- Run Main.py
If you download a .zip file from the releases section:
- Extract the zip folder to a location of your choosing
- You do not have to download any dependencies, they come pre-installed with the .exe!
-  From here you can either run the "Launcher.vbs' file or navigate to dist>MyDisk>>MyDisk.exe
-  You can create your own shortcut for MyDisk.exe if you'd like.

HOW TO BUNDLE SOURCECODE TO .exe
Requirements: Python, pyinstaller, basic coding knowledge
- If you do not have pyinstaller, open command prompt and run pip installer pyinstaller
Bundling:
- Clone the repository
- Open a command prompt in the folder you cloned to
- In command prompt, run "pyinstaller MyDisk.spec"
- Move the art folder to dist>MyDisk
- .exe file will be in dist>MyDisk>MyDisk.exe
- (Optional) create a shortcut for MyDisk.exe
If you do not have experience with bundling application or python in general, I recommend downloading the stand-alone releases from https://github.com/IdiotStick2K/MyDisk/releases

INFORMATION REGARDING ANALYTICS TRACKING - READ
You may see scripts like analytics.py, or supabase_client.py. I have intergrated a database into my application, that logs when somebody launches the app.
I do not take any personal, or sensitive data, all that happens is your app version is taken from config.py as well as a timestamp and is sent to the database I have connected.
You can easily opt out of theses analytics in the apps settings window! I included this out of pure curiosity about how many people use the app. 
Another note: Downloading the source code will automatically opt you out of analytics tracking, because I removed my database key and URL from the config.py to prevent abuse.
If you have any questions about where the data goes or anything else, please DM me on discord! @.idiotstick or email me idiotstickbusiness@gmail.com


