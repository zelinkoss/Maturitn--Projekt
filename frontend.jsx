import { useEffect, useState } from "react";

function App() {
  const [cars, setCars] = useState([]);

  useEffect(() => {
    fetch("http://localhost:5000/api/cars")
      .then(res => res.json())
      .then(data => setCars(data));
  }, []);

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <h1 className="text-2xl font-bold mb-4">Autobazar</h1>
      <ul>
        {cars.map(car => (
          <li key={car.id} className="mb-2 p-3 bg-white rounded shadow">
            {car.brand} {car.model} – {car.price} Kč
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
