Description: Automation of LED corridor lights changes based on set time via python script. The idea behind this project was to elevate the work for the environment control team on the ship since they allegedly had to manually change approximately 1400 cabin lights for passenger that are placed on the front side of the door on the ceiling 3 times a day via some unfinished software. This script simply reads all the IP addresses given from the .txt file that are on the ship and calls asyncrounously PLC functions via web link to change the LED lights. It was created in a way that the user can set up custom times for morning, afternoon and evening for desired changes. They can also be instantly changed manually if needed or just let be automatically for the given time.


Title: Corridor Lights Controller (CLC)  
Desc: Automated python script for PLC corridor light color changes  
Current Ver 2.4  
---
v2.1 - Fixes and enchancments:  
- code entirely reconstructed and polished
- added docstrings
- added types
- swapped elifs for match/case

v2.2 - Fixes and enchancments:  
- folder structure refactored
- added error handler func

v2.3 - Fixes and enchancments:  
- UI update on system behaviour changes made more seamless
- repetitive prints stored in seperate funcs for cleaner code

v2.4 - Fixes and enchancments:  
- removed unecessary "termcolor" library for console text coloring
- refactored and optimized "exec_light_change" function
- added "light_execution_status" function for clearer UI and info after each light execution
- added detailed cabin information (cabin number - cabin ip) when it fails to change the light
- added additional info about current lights and upcoming light schedule changes
- added execution status when the lights are being changed
- updated and adjusted overall UI
- fixed error logging and changed system behavior when it crashes

Known issuses:  
- on key press for manual, it displays pressed keys for next input

To be added:  
- loading dots, instead of every 15 min time display
- copying predefined settings files from ip, time and logs on py compile (ambigious)
- option to change light colors (RGB)