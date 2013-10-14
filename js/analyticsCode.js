//Loads google analytics code
(function(i,s,o,g,r,a,m){i['GoogleAnalyticsObject']=r;i[r]=i[r]||function(){
(i[r].q=i[r].q||[]).push(arguments)},i[r].l=1*new Date();a=s.createElement(o),
m=s.getElementsByTagName(o)[0];a.async=1;a.src=g;m.parentNode.insertBefore(a,m)
})(window,document,'script','//www.google-analytics.com/analytics.js','ga');

//determines which analytics to run based on the domain
if(document.URL=="http://shoefind.appspot.com/"){ga('create', 'UA-43201587-1', 'shoefind.appspot.com');}
else{ga('create', 'UA-43377715-1', 'projectperfectshoe.com');}

//sends page view to appengine
ga('send', 'pageview');

//array function that lets us search arrays included here for IE (windows phone) support.
if (!Array.prototype.indexOf) {
  Array.prototype.indexOf = function (searchElement /*, fromIndex */ ) {
    'use strict';
    if (this == null) {
      throw new TypeError();
    }
    var n, k, t = Object(this),
        len = t.length >>> 0;

    if (len === 0) {
      return -1;
    }
    n = 0;
    if (arguments.length > 1) {
      n = Number(arguments[1]);
      if (n != n) { // shortcut for verifying if it's NaN
        n = 0;
      } else if (n != 0 && n != Infinity && n != -Infinity) {
        n = (n > 0 || -1) * Math.floor(Math.abs(n));
      }
    }
    if (n >= len) {
      return -1;
    }
    for (k = n >= 0 ? n : Math.max(len - Math.abs(n), 0); k < len; k++) {
      if (k in t && t[k] === searchElement) {
        return k;
      }
    }
    return -1;
  };
}


//event send function. Special function because now we have a central place to log & control how events are sent to GA
function sendEvent(category, action, label, value){
	productionUrl = ["http://shoefind.appspot.com/","http://shoefind.appspot.com","http://www.projectperfectshoe.com/","http://www.projectperfectshoe.com","http://www.projectperfectshoe.com/#home"];
	teamUrl = "1."
	stagingUrl = "2.";
	if(document.URL.indexOf(teamUrl)>=0||document.URL.indexOf(stagingUrl)>=0){
		console.log('Event triggered but not sent to GA-admin');
	}
	else if(productionUrl.indexOf(document.URL)>=0){
		ga('send', 'event', category, action, label, value);
		console.log('Event Sent to GA');
	}
	else{
		console.log('Event triggered but not sent to GA');
	}
}

//=================
//Clicks to track |
//=================

$('#toggle-wishlist').click(function(){
	sendEvent('ux', 'click', 'wishlist');
})

$('#logo').click(function(){
	sendEvent('ux', 'click', 'logo');
})

$('.ui-dialog-contain img').click(function(){
	sendEvent('ux', 'click', 'instructionsOK');
})

$('.remove').on('click', function(){
	//this was causing bugs, so I've disabled it for now
	//sendEvent('ux', 'click', 'deleteItem');
})
