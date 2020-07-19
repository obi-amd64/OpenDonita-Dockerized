# OpenDoñita

OpenDoñita is a server designed to work with the **Conga 1490/1590** robotic vacuum cleaners distributed by **Cecotec**
in Spain. Since it is really a robot manufactured by the chinese company **robot bona**, it is very probable that it
would work with other robots.

All the documentation is in my personal blog: https://blog.rastersoft.com/?p=2324 (in spanish).

## Using OpenDoñita

To use it, you must first install your own DNS server in your internal network. I used a Raspberry Pi with *dnsmasq* and
*hostapd* to build an isolated WiFi network, but in normal operation it is enough to launch *dnsmasq* and redirect the DNS
petitions from your WiFi router to the Raspberry.

Now, in the computer with the DNS, edit the file */etc/hosts* and add these two entries:

* 192.168.X.Y    bl-app-eu.robotbona.com
* 192.168.X.Y    bl-im-eu.robotbona.com

being 192.168.X.Y the IP address of the computer where the server will run (usually it should be the Raspberry Pi too).
This is a must because the robot connects to a server in those domains (which this project replaces), to receive from
them the commands. The official Android/iPhone app doesn't send commands directly to the robot, but only to the server,
and it resends them to the robot. Thus, to allow our local server to pose as the official one, we must redirect those
two domains to our own computer.

IMPORTANT: the new server requires Python 3.6 or later. Raspbian has Python 3.7, but OSMC, at the time of writting this,
has Python 3.5. Take it into account if you want to reuse a RPi that you are already using.

Now restart *dnsmasq* with *sudo systemctl restart netmasq* to ensure that it re-reads the configuration.

The next step is to change the DNS in your WiFi router to point to the Raspberry if you aren't using an isolated WiFi
network. This is dependant on your specific router.

After doing this, entering those domains in your browser should return an error.

Now, copy all the files of this project in the computer choosen to be your own server, and launch it with:

    sudo ./congaserver.py

It is important to launch it as root because it needs to bind to the port 80, and only root can do that. Also, if you
want to be able to close your ssh connection with the Raspberry, you should launch it using *nohup* (or *screen*
if you want to check it out):

    sudo screen ./congaserver.py

and detach by pressing *Ctrl+a*, then *d*. To reatach, just do

    sudo screen -r

Now you can check if everything works by opening any of the previous domains in your browser. You should see this page:

![The new app](capture1.png)

## Connecting the robot to the new server

Now there are two ways of connecting the robot to the server:

* turn off the WiFi router and turn on again (or stop *hostapd*, wait some seconds, and start it again if you are using
an isolates WiFi network)

* or turn off the robot for some seconds and turn on it again. This requires removing it from the charging base and
turning it off with the lateral switch.

when you do it, you should see that, after several seconds, the Wifi light in the robot turns on, and in the server
screen there are several messages. Now you can control it from the new app.

## Using the app

In the main screen you have four buttons:

The *home* button: when it is filled of color, it means that the robot is not in the base. Clicking on it will send it
to the charger.

The *play* button: this triangle starts a new clean cycle, and will change to a square (or *stop*) button, which will
stop the clean cycle.

The *sound* button: this is an speaker, and pressing on it enables or disables the *beeps* emited by the robot.

The *settings* button: this button will open a popup where it is possible to choose the fan power, the water flux, and
the clean mode:

![The settings popup](capture2.png)

This configuration will be remembered even if the robot is turned off and on again.

## Pairing the robot manually

To pair the robot you need a computer with a WiFi adapter. First, put your robot in *pairing mode* by pressing the power
button until it sends a beep. The Wifi light will blink.

Now, in your computer, search for a WiFi network called *CongaGyro_XXXXXX* (if you are using a robot from another distributor,
the Wifi SSID can change) and connect to it (it has no password).

After connecting, run *./configconga.py WIFI_SSID WIFI_PASSWORD* (being WIFI_SSID and WIFI_PASSWORD the SSID and the password
of your Wifi network).

After about two seconds, your computer will be disconnected from that network, and the robot will connect to your WiFi.

## Author

Sergio Costas  
http://www.rastersoft.com  
rastersoft@gmail.com  
