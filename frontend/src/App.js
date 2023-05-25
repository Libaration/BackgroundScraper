import logo from "./logo.svg";
import "./App.css";
import { socket } from "./socket";
import { useEffect, useState } from "react";
function App() {
  const [id, setId] = useState("");
  const [response, setResponse] = useState([]);
  const renderResponse = () => {
    return response.map((property) => {
      return Object.keys(property).map((key) => {
        return (
          <div>
            <h2>{key}</h2>
            <p>{property[key]}</p>
          </div>
        );
      });
    });
  };
  useEffect(() => {
    socket.on("connect", () => {
      console.log(socket.id);
      setId(socket.id);
    });
    socket.on("baltimore_county_scrape_result", (data) => {
      console.log(data);
    });
    socket.on("test", (data) => {
      console.log("Received test event:", data);
    });

    return () => {
      socket.off("connect");
      socket.off("baltimore_county_scrape_result");
    };
  }, []);

  return (
    <div className="App">
      <h1>Socket ID: {id}</h1>
      <button
        onClick={() =>
          socket.emit("scrape_baltimore_county", {
            addresses: [
              "920 S Conkling St",
              "3430 MCSHANE WAY",
              "3438 MCSHANE WAY",
              "3548 MCSHANE WAY",
              "920 S Conkling St",
              "3430 MCSHANE WAY",
              "3438 MCSHANE WAY",
              "3548 MCSHANE WAY",
              "920 S Conkling St",
            ],
          })
        }
      >
        Scrape Baltimore County Property
      </button>
      {renderResponse()}
    </div>
  );
}

export default App;
