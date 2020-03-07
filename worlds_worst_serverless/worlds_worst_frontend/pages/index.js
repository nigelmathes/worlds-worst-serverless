import Head from 'next/head'
import Style from '../components/Style';
import axios from 'axios';
import Typist from 'react-typist';
import React, {useState} from "react";

const Home = props => {
    const [name, setName] = useState(props.player.Player.name);
    const [message, setMessage] = useState([]);
    const [input, setInput] = useState("");

    const setField = e => {
        setInput(e.currentTarget.value);
    };

    const sendLine = async e => {
        e.preventDefault();

        const inputs = {
            action: input,
            playerId: "player_hash",
            enhanced: false,
        };
        const req = await axios.post(
            'https://aiexd2xz1m.execute-api.us-east-1.amazonaws.com/dev/route',
            inputs
        );
        const output = await req.data;
        setMessage(output.message);
        setName(output.Player.name);
        setInput("")
    };

    return (
        <div className="container">
            <Head>
                <title>World's Worst Game</title>
                <link rel="icon" href="/favicon.ico"/>
            </Head>

            <Style/>
            <main>
                <Typist
                    className="title"
                    avgTypingDelay={40}
                    startDelay={200}
                    cursor={{hideWhenDone: true}}
                >
                    Welcome to the world's worst game
                </Typist>

                <div className="description">
                    You are {name}
                </div>

                <form onSubmit={sendLine}>
                    <input
                        className="input"
                        type="input"
                        name="input"
                        value={input}
                        placeholder="Type something"
                        onChange={setField}
                        autocomplete="off"
                    />
                </form>

                {message.map((item, i) => (
                    <div className="actions" key={i}>
                        {item}
                    </div>
                ))}
            </main>
        </div>
    )
};

Home.getInitialProps = async function () {
    const inputs = {
        action: "get player info",
        playerId: "player_hash",
        enhanced: false,
    };
    const response = await axios.post('https://aiexd2xz1m.execute-api.us-east-1.amazonaws.com/dev/route', inputs);
    const output = await response.data;

    return {
        player: output
    }
};

export default Home;
