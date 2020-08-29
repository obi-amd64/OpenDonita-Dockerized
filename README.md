# OpenDoñita

OpenDoñita is a server designed to work with the **Conga 1490/1590** robotic vacuum cleaners distributed by **Cecotec**
in Spain. Since it is really a robot manufactured by the chinese company **robot bona**, it is very probable that it
would work with other robots.

All the documentation is in my personal blog: https://blog.rastersoft.com/?p=2324 (in spanish).

## Dependencies

The server requires python 3.5 or greater and the *iot-upnp* module. It can be installed with

    sudo python3 -m pip install iot-upnp

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

Now, copy all the files of this project in the computer choosen to be your own server, and install it with:

    sudo ./install.sh

After doing this, it will be installed in /opt/congaserver, a new systemd service will be created and enabled (which will
be useful if the board reboots), but you still will have to launch it manually the first time with:

    sudo systemctl start congaserver.service

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

The *settings* button: this button will open a popup where it is possible to choose the fan power, the water flux, and
the clean mode:

![The settings popup](capture2.png)

This configuration will be remembered even if the robot is turned off and on again.

During cleaning, the app will generate the map in real time:

![Map example](capture3.png)

## Using the Android App

The Android app is available in a separate repository: https://gitlab.com/rastersoft/opendonita_android

It is just a simple WebView-based app, which uses the uPnP announcements of the main server to automagically locate it
in the network and open the web app.

## Pairing the robot manually

To pair the robot you need a computer with a WiFi adapter. First, put your robot in *pairing mode* by pressing the power
button until it sends a beep. The Wifi light will blink.

Now, in your computer, search for a WiFi network called *CongaGyro_XXXXXX* (if you are using a robot from another distributor,
the Wifi SSID can change) and connect to it (it has no password).

After connecting, run *./configconga.py WIFI_SSID WIFI_PASSWORD* (being WIFI_SSID and WIFI_PASSWORD the SSID and the password
of your Wifi network).

After about two seconds, your computer will be disconnected from that network, and the robot will connect to your WiFi.

## REST API

The server offers a REST API and a full HTTP server running at port 80. It recognizes the following paths and objects:

* **/baole-web/common/sumbitClearTime.do**: part of connecting negotiation process
* **/baole-web/common/getToken.do**: part of connecting negotiation process
* **/baole-web/common/**: part of connecting negotiation process
* **/robot**: commands for managing and controlling the robots
* **anything else**: the file will be searched in the *html* folder

Under the **robot** path you can use **/robot/list** to get a list of the currently available robots connected to the server.
It returns a JSON with the following structure:

    {
        "error":0,
        "value": ["robot_1", "robot_2"...]
    }

The *value* field contains a list with zero or more strings. Each string is a robot identifier, which can be used in the
other commands.

To send an specific command to a robot, you use a path with the following format:

    /robot/robot_id/command

or, if the command requires parameters, then:

    /robot/robot_id/command?param1=value1&param2=value2...

In both cases, *robot_id* is an id returned by **/robot/list**, but can be replaced with *all*, and the command will be sent
to all the robots currently connected. The commands are stored in a queue and sent one by one to the robot.

The available commands are:

* **clean**: orders the robot to start cleaning
* **stop**: pauses the cleaning operation
* **return**: orders the robot to return to the base
* **updateMap**: orders the robot to send a map update
* **askStatus**: orders the robot to send an status update
* **notifyConnection**: notifies the robot that a web client has been opened
* **mode**: allows to set the cleaning mode. It has one parameter, *type*, with any of these values:
    * auto
    * gyro
    * random
    * borders
    * area
    * x2
    * scrub
* **fan**: sets the fan speed. It has one parameter, *speed*, with a value from 0 to 3 (bigger value means more speed)
* **watertank**: sets the watertank speed. It has one parameter, *speed*, with a value from 0 to 3 (bigger value means more speed)
* **sound**: allows to enable or disable the buzzer. It has one parameter, *status*, with a zero value to disable it, or one value
to enable it.
* **wait**: allows to wait a configurable number of seconds before continuing executing the commands in the queue. It has one parameter,
*seconds*, with a float/integer value expressing the number of seconds to wait.
* **waitState**: allows to wait for the robot to be in an specific state before continuing executing the commands in the queue. It has one parameter, *state*, which can have any of these values:
    * cleaning
    * stopped
    * returning
    * charging
    * charged
    * home

## Author

Sergio Costas  
http://www.rastersoft.com  
rastersoft@gmail.com  
