function FBLogin(){
  FB.login(function(response) {
   if (response.authResponse) {
     console.log('Welcome!  Fetching your information.... ');
     FB.api('/me', function(response) {
		goHome();
     });
   } else {
     console.log('User cancelled login or did not fully authorize.');
   }
 });

}

function goHome(){
	$.mobile.changePage("#home");	
}


$('#fbLoginBtn').click(function(){
	FBLogin();
});

$('#inviteFriend').click(function(){
	FBLogin();
});
