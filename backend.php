import express from "express";
import cors from "cors";

const app = express();
app.use(cors());
app.use(express.json());

let cars = [
  { id: 1, brand: "Škoda", model: "Octavia", price: 250000 },
  { id: 2, brand: "BMW", model: "3 Series", price: 450000 },
];

app.get("/api/cars", (req, res) => res.json(cars));
app.post("/api/cars", (req, res) => {
  const newCar = req.body;
  cars.push(newCar);
  res.status(201).json(newCar);
});

app.listen(5000, () => console.log("Server běží na http://localhost:5000"));
