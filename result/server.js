const express = require('express');
const async = require('async');
const { Pool } = require('pg');
const cookieParser = require('cookie-parser');
const path = require('path'); // Added path module
const http = require('http');
const socketIo = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

const port = process.env.PORT || 4000;

// Socket.io connection
io.on('connection', (socket) => {
    socket.emit('message', { text: 'Welcome!' });

    socket.on('subscribe', (data) => {
        socket.join(data.channel);
    });
});

// PostgreSQL connection pool
const pool = new Pool({
    connectionString: 'postgres://postgres:postgres@db/postgres',
});

// Retry connecting to the database
async.retry(
    { times: 1000, interval: 1000 },
    (callback) => {
        pool.connect((err, client, done) => {
            if (err) {
                console.error("Waiting for db...");
            }
            callback(err, client);
        });
    },
    (err, client) => {
        if (err) {
            return console.error("Giving up after multiple attempts:", err);
        }
        console.log("Connected to db");
        getVotes(client);
    }
);

// Function to retrieve votes from the database
function getVotes(client) {
    client.query('SELECT vote, COUNT(id) AS count FROM votes GROUP BY vote', [], (err, result) => {
        if (err) {
            console.error("Error performing query:", err);
        } else {
            const votes = collectVotesFromResult(result);
            io.sockets.emit("scores", JSON.stringify(votes));
        }

        // Set a timeout to fetch votes again
        setTimeout(() => getVotes(client), 1000);
    });
}

// Function to collect votes from the query result
function collectVotesFromResult(result) {
    const votes = { a: 0, b: 0 };

    result.rows.forEach((row) => {
        votes[row.vote] = parseInt(row.count, 10); // Specify radix for parseInt
    });

    return votes;
}

// Middleware
app.use(cookieParser());
app.use(express.urlencoded({ extended: true })); // Added 'extended: true' for better parsing
app.use(express.static(path.join(__dirname, 'views'))); // Updated to use path.join

// Route for serving the main page
app.get('/', (req, res) => {
    res.sendFile(path.resolve(__dirname, 'views', 'index.html')); // Updated path
});

// Start the server
server.listen(port, () => {
    console.log(`App running on port ${port}`);
});
