google.charts.load('current', {'packages':['gauge']});
google.charts.setOnLoadCallback(drawChart);

var fireHeading = document.getElementById("fireHeading");

// Get reference to database.
var firebaseHeadingRef = firebase.database().ref().child("Heading");

// Listen to value events
firebaseHeadingRef.on('value', function(datasnapshot){
  fireHeading.innerText = datasnapshot.val();
});

google.charts.load('current', {'packages':['gauge']});



function drawChart() {

  var data = google.visualization.arrayToDataTable([
    ['Label', 'Value'],
    ['', 68]
  ]);

  var options = {
    animation:{
      duration: 800,  // Default: 400
      easing: 'inAndOut', // Default: linear
    },
    // width: 400,  // Default: Container's width
    // height: 100, // Default: Container's width
    redFrom: 90, redTo: 100,
    yellowFrom:75, yellowTo: 90,
    minorTicks: 5
  };

  var chart = new google.visualization.Gauge(document.getElementById('chartDiv'));
  var button = document.getElementById('refreshBtn');

  var firebaseCurrentTemperature = firebase.database().ref().child("Current Temperature");

  chart.draw(data, options);

  // Listen to temperature value events
  firebaseCurrentTemperature.on('value', function(datasnapshot){
    data.setValue(0, 1, datasnapshot.val());
  });

  chart.draw(data, options);


}
