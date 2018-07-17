google.charts.load('current', {'packages':['gauge']});
google.charts.setOnLoadCallback(init);
var fireHeading = document.getElementById("fireHeading");

// Get reference to database.
var firebaseHeadingRef = firebase.database().ref().child("Heading");

// Listen to value events
firebaseHeadingRef.on('value', function(datasnapshot){
  fireHeading.innerText = datasnapshot.val();
});

function init() {

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

  var data = google.visualization.arrayToDataTable([
    ['Label', 'Value'],
    ['', 68]
  ]);

  var chart = new google.visualization.Gauge(document.getElementById('chartDiv'));
  var button = document.getElementById('refreshBtn');

  function drawChart() {
    // Disabling the button while the chart is drawing.
    button.disabled = true;
    google.visualization.events.addListener(chart, 'ready',
      function() {
        button.disabled = false;
      });
    chart.draw(data, options);
  }

  button.onclick = function() {
    data.setValue(0, 1, 30 + Math.round(20 * Math.random()));
    chart.draw(data, options);
    drawChart();
  }

  drawChart();

}
