{
  get_telop: function(telops, time=null) {
	if(time === null){
		time = thisLayer.time;
	}
	for(i in telops) {
		var o = telops[i];
		var start = o[0];
		var duration = o[1];
		var message = o[2];
		if(start <= time && time < start + duration){
			return message;
		}
	}
	return "";
  }
}
