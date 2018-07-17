var mainText = document.getElementById("mainText");
var submitBtn = document.getElementById("submitBtn");
var fireHeading = document.getElementById("fireHeading");

// Get reference to database.
var firebaseHeadingRef = firebase.database().ref().child("Heading");

// Listen to value events
firebaseHeadingRef.on('value', function(datasnapshot){
  fireHeading.innerText = datasnapshot.val();
});

function submitClick() {

  var firebaseRef = firebase.database().ref();

  var messageText = mainText.value;

  firebaseRef.push().set(messageText);

}
