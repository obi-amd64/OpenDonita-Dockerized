$(document).ready(function(){
    $(document).powerWater = new PowerWater();
});

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

        $(window).resize(function() {
            this._last_map = "";
            this._last_track = "";
            this._set_sizes();
        }.bind(this));

        for(let x=0; x<4; x++) {
            let name = `#fan_${x}`;
            $(name).click(function() {
                this._set_fan(x, true);
            }.bind(this));
            name = `#water_${x}`;
            $(name).click(function() {
                this._set_water(x, true);
            }.bind(this));
        }
        for(let x=0; x<7; x++) {
            let name = `#mode_${x}`;
            $(name).click(function() {
                this._set_mode(x, true);
            }.bind(this));
        }

        $("#audio").click(function () {
            let status;
            if (this._audio) {
                status = 0;
            } else {
                status = 1;
            }
            $.getJSON(`robot/all/sound?status=${status}`);
        }.bind(this));

        $("#back").click(function () {
            $("#div_settings").hide();
        });

        $("#settings").click(function () {
            $("#div_settings").show();
        });
        $("#div_settings").hide();

        $("#home").click(function () {
            if (this._allowHome) {
                $.getJSON(`robot/${this._robot}/return`);
            }
        }.bind(this));

        $("#startstop").click(function () {
            if (this._allowStart) {
                this._read_defaults(true);
                $.getJSON(`robot/${this._robot}/clean`);
            } else if (this._allowStop) {
                $.getJSON(`robot/${this._robot}/stop`);
            }
        }.bind(this));
        this._set_sizes();
        this._read_defaults(false);
        this._update_status();
        //$.getJSON(`robot/${this._robot}/notifyConnection`);
        setInterval(this._update_status.bind(this), 1000);
    }

    _store_value(name, value) {
        this._values[name] = value;
        $.getJSON(`robot/${this._robot}/setProperty?key=${name}&value=${value}`);
    }

    _read_value(name, cb) {
        $.getJSON(`robot/${this._robot}/getProperty?key=${name}`).done(function (received) {
            if (received['error'] == 0) {
                this._values[name] = received['value'][name];
            } else {
                this._store_value(name, this._values[name]);
            }
            cb(this._values[name]);
        }.bind(this));
    }

    _read_defaults(update) {
        this._read_value('fan', function(value) {
            this._set_fan(value, update);
        }.bind(this));

        this._read_value('water', function(value) {
            this._set_water(value, update);
        }.bind(this));

        this._read_value('mode', function(value) {
            this._set_mode(value, update);
        }.bind(this));
    }

    _update_status() {
        $.getJSON(`robot/${this._robot}/getStatus`).done(function (received) {
            if (received['error'] != 0) {
                return;
            }
            // audio enabled/disabled
            if (received['value']['voice'] == "2") {
                this._audio = true;
            } else {
                this._audio = false;
            }
            this._set_audio(false);

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
            if (mode == 1) {
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
        }.bind(this));
    }

    _set_sizes() {
        let width = $("#div_settings").width();
        let height = $("#div_settings").height();
        let minimum = width;
        if (width > height) {
            minimum = height;
        }

        let w = minimum / 4;
        w = w * 0.95
        for(let x=0; x<4; x++) {
            this._set_block_size(`fan_${x}`, w, w);
            this._set_block_size(`water_${x}`, w, w);
        }
        for(let x=0; x<7; x++) {
            this._set_block_size(`mode_${x}`, w, w);
        }
        this._set_block_size(`back`, w, w);

        let canvas = document.getElementById("mapcanvas");
        canvas.width = $("#map").width();
        canvas.height = $("#map").height();
    }

    _update_map(data) {
        if ((this._last_map == data['value']['map']) && (this._last_track == data['value']['track'])) {
            return;
        }
        this._last_map = data['value']['map'];
        this._last_track = data['value']['track'];
        console.log(`map: ${this._last_map}; track: ${this._last_track}`);
        let track = Uint8Array.from(atob(data['value']['track']).substring(4), c => c.charCodeAt(0))
        let map =  Uint8Array.from(atob(data['value']['map']), c => c.charCodeAt(0))
        let mapw = map[5] * 256 + map[6];
        let maph = map[7] * 256 + map[8];
        let pixels = [];
        let pos = 9;
        let repetitions = 0;

        let chargerPos = data['value']['chargerPos'].split(",");
        let chargerX = parseInt(chargerPos[0]);
        let chargerY = parseInt(chargerPos[1]);

        let minx = chargerX;
        let maxx = chargerX;
        let miny = chargerY;
        let maxy = chargerY;
        let index = 0;

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

        let radius1 = c.width / (maxx - minx + 1);
        let radius2 = c.height / (maxy - miny + 1);
        if (radius2 < radius1) {
            radius1 = radius2;
        }
        radius2 = radius1 / 2;
        let radius3 = radius2 * 0.8;

        for(let y = miny; y <= maxy; y++) {
            for(let x = minx; x <= maxx; x++) {
                let pos = x + mapw * y;
                if (pixels[pos] == 0) {
                    pos++;
                    continue;
                }
                switch (pixels[pos]) {
                    case 1:
                        ctx.fillStyle = '#0000ff';
                        break;
                    case 2:
                        ctx.fillStyle = '#ff0000';
                        break;
                }
                ctx.beginPath();
                ctx.arc((x - minx)*radius1 + radius2, (y - miny)*radius1 + radius2, radius3, 0, 2 * Math.PI);
                ctx.fill();
                pos++;
            }
        }
        ctx.fillStyle = '#00ff00';
        ctx.beginPath();
        ctx.arc((chargerX - minx)*radius1 + radius2, (chargerY - miny)*radius1 + radius2, radius3, 0, 2 * Math.PI);
        ctx.fill();
        ctx.strokeStyle = '#000000';
        ctx.lineWidth = radius3 / 2;
        let first = true;
        for(let a=0; a < track.length; a += 2) {
            let x = track[a];
            let y = track[a + 1];
            if (first) {
                ctx.moveTo((x - minx)*radius1 + radius2, (y - miny)*radius1 + radius2);
                first = false;
                continue;
            }
            ctx.lineTo((x - minx)*radius1 + radius2, (y - miny)*radius1 + radius2);
        }
        ctx.stroke();
    }

    _set_block_size(name, w, h) {
        $(`#${name}`).width(w);
        $(`#${name}`).height(h);
        $(`#pic_${name}`).width(w);
        $(`#pic_${name}`).height(h);
    }

    _set_audio(update) {
        let status;
        if (this._audio) {
            $("#audio").attr("src", "speaker_enabled.svg");
        } else {
            $("#audio").attr("src", "speaker_disabled.svg");
        }
        if (update) {
            $.getJSON(`robot/all/sound?status=${status}`);
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
