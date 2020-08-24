$(document).ready(function(){
    $(document).powerWater = new PowerWater();
});

function back_android() {
    $("#div_settings").hide();
}

class PowerWater {
    constructor() {
        this._values = {};
        this._values['fan'] = 2;
        this._values['water'] = 0;
        this._values['mode'] = 0;
        this._allowHome = false;
        this._allowStart = false;
        this._allowStop = false;
        this._audio = true;
        this._counter = 0;
        this._robot = "all";
        this._modes = ["auto", "gyro", "random", "borders", "area", "x2", "scrub"];
        this._last_map = "";
        this._last_track = "";
        this._rotation = 0;

        $(window).resize(() => {
            this._last_map = "";
            this._last_track = "";
            this._set_sizes();
        });

        $("#mapcanvas").click(() => {
            this.rotate_map();
        });

        for(let x=0; x<4; x++) {
            let name = `#fan_${x}`;
            $(name).click(() => {
                this._set_fan(x, true);
            });
            name = `#water_${x}`;
            $(name).click(() => {
                this._set_water(x, true);
            });
        }
        for(let x=0; x<7; x++) {
            let name = `#mode_${x}`;
            $(name).click(() => {
                this._set_mode(x, true);
            });
        }

        $("#audio").click(() => {
            if (this._audio) {
                var status = 0;
            } else {
                var status = 1;
            }
            $.getJSON(`robot/all/sound?status=${status}`);
        });

        $("#back").click(() => {
            $("#div_settings").hide();
        });

        $("#settings").click(() => {
            this._read_defaults();
            $("#div_settings").show();
            history.pushState({ foo: "bar" }, "page 2", "bar.html");
        });
        $("#div_settings").hide();

        $("#home").click(() => {
            if (this._allowHome) {
                $.getJSON(`robot/${this._robot}/return`);
            }
        });

        $("#startstop").click(() => {
            if (this._allowStart) {
                this._read_defaults(() => {
                    $.getJSON(`robot/${this._robot}/clean`);
                });
            } else if (this._allowStop) {
                $.getJSON(`robot/${this._robot}/stop`);
            }
        });
        this._set_sizes();
        this._read_defaults();
        this._update_status();
        $.getJSON(`robot/${this._robot}/updateMap`);
        $.getJSON(`robot/${this._robot}/notifyConnection`);
        $.getJSON(`robot/${this._robot}/askStatus`);
        setInterval(this._update_status.bind(this), 1000);
    }

    _store_value(name, value) {
        this._values[name] = value;
        $.getJSON(`robot/${this._robot}/setProperty?key=${name}&value=${value}`);
    }

    _read_defaults(cb) {
        $.getJSON(`robot/${this._robot}/getProperty`).done((received) => {
            if (received['error'] == 0) {
                for (let key in received['value']) {
                    this._values[key] = received['value'][key];
                }
                this._set_fan(this._values['fan'], false);
                this._set_water(this._values['water'], false);
                this._set_mode(this._values['mode'], false);
                if (cb) {
                    cb();
                }
            }
        });
    }

    _update_status() {
        $.getJSON(`robot/list`).done(function (received) {
            if (received['value'].length == 0) {
                $('#noconga').css('z-index', 10);
            } else {
                $('#noconga').css('z-index', 0);
            }
        });
        $.getJSON(`robot/${this._robot}/getStatus`).done((received) => {
            if (received['error'] != 0) {
                return;
            }
            console.log(received['value']['battery']);
            // audio enabled/disabled
            if (received['value']['voice'] == "2") {
                this._audio = true;
            } else {
                this._audio = false;
            }
            this._set_audio();

            // mode
            let mode = received['value']['workState'];
            if ((mode == 4) || (mode == 5) || (mode == 6)) {
                this._allowHome = false;
                $("#home").attr("src", "home_disabled.svg");
            } else {
                this._allowHome = true;
                $("#home").attr("src", "home_enabled.svg");
            }
            if ((mode == 2) || (mode == 5) || (mode == 6)) {
                this._allowStart = true;
            } else {
                this._allowStart = false;
            }
            if ((mode == 1) || (mode == 4)) {
                this._allowStop = true;
            } else {
                this._allowStop = false;
            }
            if (this._allowStart) {
                $("#startstop").attr("src", "play_enabled.svg");
            } else {
                if (this._allowStop) {
                    $("#startstop").attr("src", "stop_enabled.svg");
                } else {
                    $("#startstop").attr("src", "play_disabled.svg");
                }
            }
            if (mode == 5) {
                $("#charging").show();
            } else {
                $("#charging").hide();
            }
            let bat_level = received['value']['battery'];
            let aspect = $('#battery').width() / $('#battery').height();
            if (aspect > 1.0) {
                $("#battery_level").css("width", `${bat_level}%`);
                $("#battery_level").css("height", "100%");
            } else {
                $("#battery_level").css("height", `${bat_level}%`);
                $("#battery_level").css("width", "100%");
            }
            if ((mode == 1) || (mode == 4)) {
                this._counter++;
                if (this._counter >= 5) {
                    // Update map each 5 seconds
                    $.getJSON(`robot/${this._robot}/updateMap`);
                    this._counter = 0;
                }
            }
            this._update_map(received);
        });
    }

    _set_sizes() {
        let width = $("#div_settings").width();
        let height = $("#div_settings").height();
        if (width > height) {
            var top = 1;
            var bottom = 1;
            let wt = (width - (5 * height / 4)) / 2;
            if (wt < 0) {
                wt = 0;
            }
            var left = Math.floor(wt);
            var right = Math.ceil(wt);
        } else {
            var left = 1;
            var right = 1;
            let wt = (height - (5 * width / 4)) / 2;
            if (wt < 0) {
                wt = 0;
            }
            var top = Math.floor(wt);
            var bottom = Math.ceil(wt);
        }
        $("#div_settings2").css("padding", `${top}px ${right}px ${bottom}px ${left}px`);

        let canvas = document.getElementById("mapcanvas");
        canvas.width = $("#map").width();
        canvas.height = $("#map").height();
    }

    _update_map(data = null) {
        if (data != null) {
            if ((this._last_map == data['value']['map']) && (this._last_track == data['value']['track'])) {
                return;
            }
            this._last_map = data['value']['map'];
            this._last_track = data['value']['track'];
            this._chargerPos = data['value']['chargerPos'].split(",");
        }
        //console.log(`map: ${this._last_map}; track: ${this._last_track}`);
        let track = Uint8Array.from(atob(this._last_track).substring(4), c => c.charCodeAt(0))
        let map =  Uint8Array.from(atob(this._last_map), c => c.charCodeAt(0))
        let mapw = map[5] * 256 + map[6];
        let maph = map[7] * 256 + map[8];
        let pixels = [];
        let pos = 9;
        let repetitions = 0;

        let chargerX = parseInt(this._chargerPos[0]);
        let chargerY = parseInt(this._chargerPos[1]);

        let minx = chargerX;
        let maxx = chargerX;
        let miny = chargerY;
        let maxy = chargerY;
        let index = 0;
        let errorCharger = false;
        if ((chargerX == -1) || (chargerY == -1)) {
            errorCharger = true;
        }

        while(pos < map.length) {
            if ((map[pos] & 0xc0) == 0xc0) {
                repetitions *= 64;
                repetitions += map[pos] & 0x3F;
                pos++;
                continue;
            }
            if (repetitions == 0) {
                repetitions = 1;
            }
            let value = map[pos];
            pos++;
            for(let a=0; a<repetitions; a++) {
                let mul = 64;
                for(let b=0; b<4; b++) {
                    let v = (value/mul) & 0x03;
                    pixels.push(v);
                    mul /= 4;
                    if (v == 0) {
                        index++;
                        continue;
                    }
                    let x = index % mapw;
                    let y = Math.floor(index / mapw);
                    index++;
                    if (errorCharger) {
                        minx = x;
                        miny = y;
                        maxx = x;
                        maxy = y;
                        errorCharger = false;
                    } else {
                        if (x < minx) {
                            minx = x;
                        }
                        if (y < miny) {
                            miny = y;
                        }
                        if (x > maxx) {
                            maxx = x;
                        }
                        if (y > maxy) {
                            maxy = y;
                        }
                    }
                }
            }
            repetitions = 0;
        }
        pos = minx + miny * mapw;
        var c = document.getElementById("mapcanvas");
        var ctx = c.getContext("2d");
        ctx.fillStyle = "#FFFFFF";
        ctx.fillRect(0, 0, c.width, c.height);
        if (minx > maxx) {
            return;
        }

        if ((this._rotation == 0) || (this._rotation == 2)) {
            var radius1 = c.width / (maxx - minx + 1);
            var radius2 = c.height / (maxy - miny + 1);
        } else {
            var radius1 = c.height / (maxx - minx + 1);
            var radius2 = c.width / (maxy - miny + 1);
        }

        if (radius2 < radius1) {
            radius1 = radius2;
        }
        radius2 = radius1 / 2;
        let radius3 = radius1 * 1.6; // each point is 20cm wide, and the robot is 32cm wide

        let nx, ny, fr1, fr2;
        for(let y = miny; y <= maxy; y++) {
            for(let x = minx; x <= maxx; x++) {
                let pos = x + mapw * y;
                if (pixels[pos] == 0) {
                    pos++;
                    continue;
                }
                switch (pixels[pos]) {
                    case 1:
                        // Wall
                        ctx.fillStyle = '#000000';
                        break;
                    case 2:
                        // Floor
                        ctx.fillStyle = '#ffff00';
                        break;
                }
                ctx.beginPath();
                //ctx.arc((x - minx)*radius1 + radius2, (y - miny)*radius1 + radius2, radius3, 0, 2 * Math.PI);
                [nx, ny, fr1, fr2] = this._rotate_coords((x - minx)*radius1, (y - miny)*radius1, radius1, c);
                ctx.fillRect(nx, ny, fr1, fr2);
                ctx.fill();
                pos++;
            }
        }
        let x;
        let y;
        ctx.lineWidth = radius3;
        let first = true;
        ctx.lineCap = "round";
        ctx.strokeStyle = '#00ffff';
        // Clean zones
        for(let a=0; a < track.length; a += 2) {
            if (!first) {
                ctx.beginPath();
                [nx, ny, fr1, fr2] = this._rotate_coords((x - minx)*radius1 + radius2, (y - miny)*radius1 + radius2, 0, c);
                ctx.moveTo(nx, ny);
            }
            x = track[a];
            y = track[a + 1];
            if (first) {
                first = false;
                continue;
            }
            [nx, ny, fr1, fr2] = this._rotate_coords((x - minx)*radius1 + radius2, (y - miny)*radius1 + radius2, 0, c);
            ctx.lineTo(nx, ny);
            ctx.stroke();
        }

        // robot position
        ctx.lineWidth = radius2 / 2;
        ctx.fillStyle = '#ff00ff';
        ctx.strokeStyle = '#000000';
        ctx.beginPath();
        ctx.arc(nx, ny, radius2 * 0.8, 0, 2 * Math.PI);
        ctx.fill();
        ctx.stroke();

        // charger
        if ((chargerX != -1) && (chargerY != -1)) {
            ctx.lineWidth = radius2 / 2;
            ctx.fillStyle = '#00ff00';
            ctx.strokeStyle = '#000000';
            ctx.beginPath();
            [nx, ny, fr1, fr2] = this._rotate_coords((chargerX - minx)*radius1 + radius2, (chargerY - miny)*radius1 + radius2, 0, c);
            ctx.arc(nx, ny, radius2 * 0.8, 0, 2 * Math.PI);
            ctx.fill();
            ctx.stroke();
        }
    }

    _rotate_coords(x, y, radius, c) {
        switch(this._rotation) {
            case 0:
                return [x, y, radius, radius];
            case 1:
                return [c.width - y, x, -radius, radius];
            case 2:
                return [c.width - x, c.height - y, -radius, -radius];
            case 3:
                return [y, c.height - x, radius, -radius];
        }
    }

    rotate_map() {
        console.log(`Rotate ${this._rotation}`);
        this._rotation++;
        if (this._rotation >= 4) {
            this._rotation = 0;
        }
        console.log(`Rotated ${this._rotation}`);
        this._last_map = "";
        this._last_track = "";
        this._update_map();
    }

    _set_audio() {
        if (this._audio) {
            $("#audio_img").attr("src", "speaker_enabled.svg");
        } else {
            $("#audio_img").attr("src", "speaker_disabled.svg");
        }
    }

    _set_water(xi, update) {
        if ((xi == 0) && (this._values['fan'] == 0)) {
            return;
        }
        for(let x=0; x<4; x++) {
            let name = `#water_${x}`;
            $(name).removeClass("powerwater_active");
        }
        let name = `#water_${xi}`;
        $(name).addClass("powerwater_active");
        if (update) {
            this._store_value('water', xi);
            $.getJSON(`robot/all/watertank?speed=${xi}`);
        }
    }

    _set_fan(xi, update) {
        if ((xi == 0) && (this._values['water'] == 0)) {
            return;
        }
        for(let x=0; x<4; x++) {
            let name = `#fan_${x}`;
            $(name).removeClass("powerwater_active");
        }
        let name = `#fan_${xi}`;
        $(name).addClass("powerwater_active");
        if (update) {
            this._store_value('fan', xi);
            $.getJSON(`robot/all/fan?speed=${xi}`);
        }
    }

    _set_mode(xi, update) {
        for(let x=0; x<7; x++) {
            let name = `#mode_${x}`;
            $(name).removeClass("powerwater_active");
        }
        let name = `#mode_${xi}`;
        $(name).addClass("powerwater_active");
        if (update) {
            this._store_value('mode', xi);
            let mode = this._modes[xi];
            $.getJSON(`robot/all/mode?type=${mode}`);
        }
    }
}
