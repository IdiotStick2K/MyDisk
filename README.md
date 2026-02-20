Thank you for using my app! Currently its very basic, but this is my first attempt at creating a usable, helpful app!
I will constantly be updating it, so watch the github repo.

HOW TO LAUNCH APP
Navigate to the dist folder and launch the "MyDisk.exe" file. From there you should see the main menu pop up. If you do not, please submit an issue on the github repository.

IMPORTANT
I am currently experimenting with background logging. I ran into many issues with this, but it does work, it just isn't perfect. When you close the application, it will minimize to your system tray. From there you can right click on the MyDisk icon and you will see open, restart, and exit. Restart and exit are similar, and end the process. Open brings back the UI. If you try and launch the .exe while an instance of the app is in your system tray, it will not work. You must either end the "MyDisk.exe" process in task manager or press exit after right clicking the icon in your system tray.

Features:
Disk info window
- See a breakdown of all mounted storage devices on your PC. You can view stuff such as capacity, model number, firmware version, and a few other things.

Disk storage logs
- Every 10 minutes, the application will automatically capture a snapshot of all of your mounted devices.
- View a disk usage history.
- Ability to change zoom and view different areas of the data.
- Matplotlib charts for easy data viewing!

Tools menu
- Manually take a disk snapshot. Helpful if you want to take a snapshot now instead of waiting the 10 minutes.

Other info
- The application will not take a snapshot if your disks have not changed by at least 50 MB. 
This is to prevent a massive amount of logs being created when you aren't doing anything, or your computer is caching stuff.
- Many more tools and features will be added in the near future!

Planned features
- Settings menu (In the works)
- Themes
- more graphs
+ more quality of life features.
