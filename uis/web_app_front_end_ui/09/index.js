// Load the Visualization API and the gauge package.
google.charts.load('current', {'packages':['gauge'], 'language': 'sv'});

// Set a callback to run when the Google Visualization API is loaded.
google.charts.setOnLoadCallback(drawGauge);

// Google Charts Configuration Options - Gauge
var gaugeOptions = {
  // animation:{             // animation.startup is not available for Gauge.
  //   duration: 1000,        // Default: 400
  //   easing: 'inAndOut',   // Default: linear
  // },
  // forceIFrame: false,     // Draws the chart inside an inline frame. (Note that
                          // on IE8, this option is ignored; all IE8 charts are
                          // drawn in i-frames.) Default: false
  greenColor: '#109618',  // The color to use for the green section, in HTML
                          // color notation. Default: '#109618'
  greenFrom: 'none',      // The lowest value for a range marked by a green
                          // color. Default: 'none'
  greenTo: 'none',        // The highest value for a range marked by a green
                          // color. Default: 'none'
  // height: 100,            // Default: Container's width
  majorTicks: ['-40','-30','-20','-10','0','10','20','30','40'],
                          // Labels for major tick marks. The number of
                          // labels define the number of major ticks in all
                          // gauges. The default is five major ticks, with
                          // the labels of the minimal and maximal gauge
                          // value. Default: 'none'
  max: 40,               // The maximal value of a gauge. Default: 100
  min: -40,                 // The minimal value of a gauge. Default: 0
  minorTicks: 5,          // The number of minor tick section in each major
                          // tick section. Default: 2
  // redColor: '#DC3912',    // The color to use for the red section, in HTML
                          // color notation. Default: '#DC3912'
  redFrom: 90,            // The lowest value for a range marked by a red
                          // color. Default: 'none'
  redTo: 100,             // The highest value for a range marked by a red
                          // color. Default: 'none'
  // width: 400,             // Default: Container's width
  // yellowColor: '#FF9900', // The color to use for the yellow section, in HTML
                          // color notation. Default: '#FF9900'
  yellowFrom:75,          // The lowest value for a range marked by a yellow
                          // color. Default: 'none'
  yellowTo: 90            // The highest value for a range marked by a yellow
                          // color. Default: 'none'
};

// Global Variables
var gauge = null;
var gaugeData;
var temperature;

// Callback that creates and populates a data table, instantiates the gauge
// chart and draws it.
function drawGauge() {
  // https://developers.google.com/chart/interactive/docs/gallery/gauge

  // Instantiate and draw the Gauge.
  if (gauge === null) {
    gauge = new google.visualization.Gauge(document.getElementById('gaugeDiv'));

    // Data with init values.
    gaugeData = new google.visualization.arrayToDataTable([
      ['Label', 'Value'],
      ['\xB0C', 0]
    ]);

    // Event listener
    google.visualization.events.addOneTimeListener(gauge, 'ready', function () {
      gaugeData = new google.visualization.arrayToDataTable([
        ['Label', 'Value'],
        ['°C', 0]
      ]);
      gauge.draw(gaugeData, gaugeOptions);
    });

  } else {

    // Update data with new value (when already initiated).
    gaugeData = new google.visualization.arrayToDataTable([
      ['Label', 'Value'],
      ['°C', temperature]
    ]);
  }

  gauge.draw(gaugeData,gaugeOptions)
}

// Get reference to database.
var firebaseCurrentTemperatureRef = firebase.database().ref().child("Current Temperature");

// Listen to value events
firebaseCurrentTemperatureRef.on('value', function(datasnapshot){
  temperature = datasnapshot.val();
  drawGauge();
  console.log(temperature);
});
