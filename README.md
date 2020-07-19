# OpenDoñita

OpenDoñita is a server designed to work with the **Conga 1490/1590** robotic vacuum cleaners distributed by **Cecotec**
in Spain. Since it is really a robot manufactured by the chinese company **robot bona**, it is very probable that it
would work with other robots.

All the documentation is in my personal blog: https://blog.rastersoft.com/?p=2324 (in spanish).

## Using OpenDoñita

To use it, you must first install your own DNS server in your internal network. I used a Raspberry Pi with *hostapd*.

Now, in the computer with the DNS, edit the file */etc/hosts* and add these two entries:

* 192.168.X.Y    bl-app-eu.robotbona.com
* 192.168.X.Y    bl-im-eu.robotbona.com

being 192.168.X.Y the IP address of the computer where the server will run (usually it should be the Raspberry Pi too).
This is a must because the robot connects to a server in those domains (which this project replaces), to receive from
them the commands. The Android/iPhone app doesn't send commands directly to the robot, but only to the server, and it
redirects them to the robot. Thus, to allow our local server to pose as the official one, we must redirect those two
domains to our own computer.

Now restart *hostapd* with *sudo systemctl restart hostapd* to ensure that it re-reads the configuration.

The next step is to change the DNS in your WiFi router to point to the *hostapd*. This is dependant on your specific router.

After doing this, entering those domains in your browser should return an error.

Now, copy all the files of this project in the computer choosen to be your own server, and launch it with:

    sudo ./congaserver.py

It is important to launch it as root because it needs to bind to the port 80, and only root can do that.

Now you can check if everything works by opening any of the previous domains in your browser. You should see this page:

![capture1.png]
