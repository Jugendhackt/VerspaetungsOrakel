let train = document.getElementById("train-id").value;
let station = document.getElementById("station-id").value;
fetch("/api/submit", {
  method: "POST",
  body: JSON.stringify({
    train: name,
    station: name,
  }),
  headers: {
    "Content-type": "application/json; charset=UTF-8"
  }
})
  .then((response) => response.json())
  .then((json) => console.log(json));
