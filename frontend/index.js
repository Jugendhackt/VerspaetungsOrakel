function postRequest() {
  let train = document.getElementById("train-id").value
  let station = document.getElementById("station-id").value;

  fetch("https://172.16.7.194:5000/api/submit", {
  method: "POST",
  body: JSON.stringify({
      train: train,
      station: station,
  }),
  headers: {
      "Content-type": "application/json; charset=UTF-8",
      'Access-Control-Allow-Origin':'*'

  }
  })
  .then((response) => response.json())
  .then((json) => console.log("hi"));
}

function displayResult() {
  // let resultfield = document.getElementById("result");
  document.getElementById("result").innerHTML = json;
}