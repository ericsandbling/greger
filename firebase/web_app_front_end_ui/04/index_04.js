$(document).ready(function(){

  var rootRef = firebase.database().ref().child("Users");

  rootRef.on("child_added", snap => {

    alert(snap.val());

  })

});
