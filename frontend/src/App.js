import logo from "./logo.svg";
import "./App.css";
import { socket } from "./socket";
import { useEffect, useState } from "react";
function App() {
  const [id, setId] = useState("");
  const [response, setResponse] = useState([]);
  const renderResponse = () => {
    console.log(response);
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
    return () => {
      socket.off("connect");
    };
  }, []);

  return (
    <div className="App">
      <h1>Socket ID: {id}</h1>
      <button
        onClick={() =>
          socket.emit(
            "scrape_baltimore_county",
            {
              addresses: ["920 S Conkling St"],
            },
            (response) => {
              setResponse(response);
            }
          )
        }
      >
        Scrape Baltimore County Property
      </button>
      {renderResponse()}
    </div>
  );
}

export default App;
