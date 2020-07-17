$(document).ready(function(){
    $(document).powerWater = new PowerWater();
});

class PowerWater {
    constructor() {
        this._fan = 2;
        this._water = 0;
        this._mode = 0;
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
        /*$("#audio").click(function () {
            this._audio_enabled = !this._audio_enabled;
            this._set_audio(true);
        }.bind(this));*/
        $("#back").click(function () {
            $("#div_settings").hide();
        });
        this._set_sizes();
    }

    _set_sizes() {
        let width = $("#div_settings").width();
        let height = $("#div_settings").height();
        let minimum = width;
        if (width > height) {
            minimum = height;
        }

        let w = minimum / 4;
        w = w * 0.97
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
        if (this._audio_enabled) {
            $("#pic_audio").attr("src", "speaker_enabled.svg");
            $("#audio").addClass("powerwater_active");
            status = "1";
        } else {
            $("#pic_audio").attr("src", "speaker_disabled.svg");
            $("#audio").removeClass("powerwater_active");
            status = "0";
        }
        if (update) {
            $.getJSON(`robot/all/sound?status=${status}`);
        }
    }

    _set_water(xi, update) {
        if ((xi == 0) && (this._fan == 0)) {
            return;
        }
        for(let x=0; x<4; x++) {
            let name = `#water_${x}`;
            $(name).removeClass("powerwater_active");
        }
        let name = `#water_${xi}`;
        $(name).addClass("powerwater_active");
        if (update) {
            $.getJSON(`robot/all/watertank?speed=${xi}`);
            this._water = xi;
        }
    }

    _set_fan(xi, update) {
        if ((xi == 0) && (this._water == 0)) {
            return;
        }
        for(let x=0; x<4; x++) {
            let name = `#fan_${x}`;
            $(name).removeClass("powerwater_active");
        }
        let name = `#fan_${xi}`;
        $(name).addClass("powerwater_active");
        if (update) {
            $.getJSON(`robot/all/fan?speed=${xi}`);
            this._fan = xi;
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
            let mode = this._modes[xi];
            $.getJSON(`robot/all/mode?type=${mode}`);
            this._mode = xi;
        }
    }
}
