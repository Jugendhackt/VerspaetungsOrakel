let train = document.getElementById("train-info").value[0];
let station = document.getElementById("train-info").value[1];

fetch("/api/submit", {
  method: "POST",
  body: JSON.stringify({
    train: train,
    station: station,
  }),
  headers: {
    "Content-type": "application/json; charset=UTF-8"
  }
})
  .then((response) => response.json())
  .then((json) => console.log(json));