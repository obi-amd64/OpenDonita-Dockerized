$(document).ready(function(){
    $(document).powerWater = new PowerWater();
});

class PowerWater {
    constructor() {
        this._values = {};
        this._values['fan'] = 2;
        this._values['water'] = 0;
        this._values['mode'] = 0;
        this._audio = true;
        this._robot = "all";
        this._modes = ["auto", "gyro", "random", "borders", "area", "x2", "scrub"];

        $(window).resize(function() {
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
            this._audio = !this._audio;
            this._set_audio(true);
        }.bind(this));

        $("#back").click(function () {
            $("#div_settings").hide();
        });

        $("#settings").click(function () {
            $("#div_settings").show();
        });
        $("#div_settings").hide();

        this._set_sizes();
        this._read_defaults();
        this._update_status();
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

    _read_defaults() {
        this._read_value('fan', function(value) {
            this._set_fan(value, false);
        }.bind(this));

        this._read_value('water', function(value) {
            this._set_water(value, false);
        }.bind(this));

        this._read_value('mode', function(value) {
            this._set_mode(value, false);
        }.bind(this));
    }

    _update_status() {
        $.getJSON(`robot/${this._robot}/getStatus`).done(function (received) {
            console.log(received);
            if (received['error'] != 0) {
                return;
            }
            if (received['value']['voice'] == "2") {
                this._audio = true;
            } else {
                this._audio = false;
            }
            this._set_audio(false);
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
            status = "1";
        } else {
            $("#audio").attr("src", "speaker_disabled.svg");
            status = "0";
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
