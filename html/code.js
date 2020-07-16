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
            this._set_table_size();
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
            this._audio_enabled = !this._audio_enabled;
            this._set_audio(true);
        }.bind(this));
        this._set_table_size();
        this._set_water(this._water, false);
        this._set_fan(this._fan, false);
        this._set_mode(this._mode, false);
        this._set_audio(false);
    }

    _set_table_size() {
        let w = window.innerWidth * 0.9;
        let h = window.innerHeight * 0.9;
        $("#div_settings").width(w);
        $("#div_settings").height(h);
        if (w > h) {
            w = h;
        } else {
            h = w;
        }
        w /= 4;
        w = w * 0.95
        for(let x=0; x<4; x++) {
            let name = `#fan_${x}`;
            $(name).width(w);
            $(name).height(w);
            name = `#pic_fan_${x}`;
            $(name).width(w);
            $(name).height(w);
            name = `#water_${x}`;
            $(name).width(w);
            $(name).height(w);
            name = `#pic_water_${x}`;
            $(name).width(w);
            $(name).height(w);
        }
        for(let x=0; x<7; x++) {
            name = `#mode_${x}`;
            $(name).width(w);
            $(name).height(w);
            name = `#pic_mode_${x}`;
            $(name).width(w);
            $(name).height(w);
        }
        $("#audio").width(w);
        $("#audio").height(w);
        $("#pic_audio").width(w);
        $("#pic_audio").height(w);
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
