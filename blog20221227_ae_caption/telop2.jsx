{
	remap: function(val, min, max, value_for_out_of_range=null) {
		/*
		* 0~1の値を指定した範囲にリマップする
		* ＠param val リマップする値
		* ＠param min リマップ前の最小値
		* ＠param max リマップ前の最大値
		* ＠param value_for_out_of_range 0~1範囲外の値に対する値
		* 	指定がない場合はminまたはmaxの値を返す
		*/
		if (val < 0) {
			val = 0;
			if (value_for_out_of_range !== null) {
				return value_for_out_of_range;
			}
		}
		else if (val > 1) {
			val = 1;
			if (value_for_out_of_range !== null) {
				return value_for_out_of_range;
			}
		}
		val = min + (max - min) * val;
		return val;
	},
	_get_telop_object: function(telops, time) {
		for(var i in telops) {
			var o = telops[i];
			var start = o[0];
			var duration = o[1]
			if(start <= time && time < start + duration){
				return telops[i];
			}
		}
		return null;
	},
	get_telop: function(telops, time=null) {
		/*
		* 特定の時間に対応するテロップデータを返す
		* 見つからなければnullを返す
		* ＠param telops テロップデータの配列
		* ＠param time 時間 指定がない場合は現在の時間を使用
		*/
		if(time === null){
			time = thisLayer.time;
		}
		var telop = this._get_telop_object(telops, time);
		if (telop === null) {
			return "";
		}
		return telop[2];
	},
	get_in_effect_ratio: function(telops, effect_sec=0.5, time=null) {
		/*
		* 特定の時間に対応するテロップデータのフェードイン率を返す
		* 見つからなければ-1を返す
		* ＠param telops テロップデータの配列
		* ＠param effect_sec テロップが表示されるまでの演出時間
		* ＠param time 時間 指定がない場合は現在の時間を使用
		*/
		if(time === null){
			time = thisLayer.time;
		}
		var telop = this._get_telop_object(telops, time);
		if(telop === null){
			return -1;
		}
		// 0 ~ 1
		var effect_ratio = Math.min((time - telop[0]) / effect_sec, 1.0);
		return effect_ratio;
	},
	get_out_effect_ratio: function(telops, effect_sec=0.5, time=null) {
		/*
		* 特定の時間に対応するテロップデータのフェードイン率を返す
		* 見つからなければ-1を返す
		* ＠param telops テロップデータの配列
		* ＠param effect_sec テロップが消えるまでの演出時間
		* ＠param time 時間 指定がない場合は現在の時間を使用
		*/
		if(time === null){
			time = thisLayer.time;
		}
		var telop = this._get_telop_object(telops, time);
		if(telop === null){
			return -1;
		}
		// 0 ~ 1
		var effect_ratio = Math.min((telop[0] + telop[1] - time) / effect_sec, 1.0);
		return 1 - effect_ratio;
	}
}
