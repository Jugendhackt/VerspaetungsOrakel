let train = document.getElementById("name").value;
let station = document.getElementById("name").value;
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
