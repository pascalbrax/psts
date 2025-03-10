# psts
Pascal Simple Temperature Server

This script parses the ```sensors``` command's output and serves the result in JSON format over HTTP at port 27315 (by default, just because 273.15 Kelvin is 0° in Celsius).

## Requirements ##
This script is tested with *Python 3.11*.
Package lm-sensors need to be installed, on Debian just run ```apt install lm-sensors```

Output example:
![image](https://github.com/user-attachments/assets/be6a61cd-837a-47b2-80c5-172693bf54cf)
