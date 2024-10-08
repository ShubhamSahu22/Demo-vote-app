using System;
using System.Data.Common;
using System.Linq;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using Newtonsoft.Json;
using Npgsql;
using StackExchange.Redis;

namespace Worker
{
    public class Program
    {
        public static int Main(string[] args)
        {
            try
            {
                // Initialize connections to PostgreSQL and Redis
                var pgsql = OpenDbConnection("Server=db;Username=postgres;Password=postgres;");
                var redisConn = OpenRedisConnection("redis");
                var redis = redisConn.GetDatabase();

                // Keep-alive query for PostgreSQL to avoid connection timeout
                var keepAliveCommand = pgsql.CreateCommand();
                keepAliveCommand.CommandText = "SELECT 1";

                // Anonymous type for deserializing vote data
                var definition = new { vote = "", voter_id = "" };

                while (true)
                {
                    // Slow down to prevent high CPU usage
                    Thread.Sleep(100);

                    // Reconnect Redis if necessary
                    if (redisConn == null || !redisConn.IsConnected)
                    {
                        Console.WriteLine("Reconnecting to Redis...");
                        redisConn = OpenRedisConnection("redis");
                        redis = redisConn.GetDatabase();
                    }

                    // Process votes from Redis queue
                    string json = redis.ListLeftPopAsync("votes").Result;
                    if (json != null)
                    {
                        var vote = JsonConvert.DeserializeAnonymousType(json, definition);
                        Console.WriteLine($"Processing vote for '{vote.vote}' by voter '{vote.voter_id}'");

                        // Reconnect PostgreSQL if necessary
                        if (pgsql.State != System.Data.ConnectionState.Open)
                        {
                            Console.WriteLine("Reconnecting to PostgreSQL...");
                            pgsql = OpenDbConnection("Server=db;Username=postgres;Password=postgres;");
                        }

                        // Update vote in the database
                        UpdateVote(pgsql, vote.voter_id, vote.vote);
                    }
                    else
                    {
                        // Execute keep-alive query if no votes found
                        keepAliveCommand.ExecuteNonQuery();
                    }
                }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"An error occurred: {ex}");
                return 1;
            }
        }

        private static NpgsqlConnection OpenDbConnection(string connectionString)
        {
            NpgsqlConnection connection = null;

            while (connection == null)
            {
                try
                {
                    connection = new NpgsqlConnection(connectionString);
                    connection.Open();
                    Console.WriteLine("Connected to PostgreSQL");
                }
                catch (SocketException)
                {
                    Console.Error.WriteLine("Waiting for PostgreSQL to be available...");
                    Thread.Sleep(1000);
                }
                catch (DbException)
                {
                    Console.Error.WriteLine("Waiting for PostgreSQL to be available...");
                    Thread.Sleep(1000);
                }
            }

            // Ensure the votes table exists
            var command = connection.CreateCommand();
            command.CommandText = @"
                CREATE TABLE IF NOT EXISTS votes (
                    id VARCHAR(255) NOT NULL UNIQUE,
                    vote VARCHAR(255) NOT NULL
                )";
            command.ExecuteNonQuery();

            return connection;
        }

        private static ConnectionMultiplexer OpenRedisConnection(string hostname)
        {
            var ipAddress = GetIp(hostname);
            Console.WriteLine($"Found Redis at {ipAddress}");

            while (true)
            {
                try
                {
                    Console.Error.WriteLine("Connecting to Redis...");
                    return ConnectionMultiplexer.Connect(ipAddress);
                }
                catch (RedisConnectionException)
                {
                    Console.Error.WriteLine("Waiting for Redis to be available...");
                    Thread.Sleep(1000);
                }
            }
        }

        private static string GetIp(string hostname)
        {
            var ipAddress = Dns.GetHostEntryAsync(hostname).Result
                              .AddressList
                              .FirstOrDefault(a => a.AddressFamily == AddressFamily.InterNetwork);

            if (ipAddress == null)
            {
                throw new Exception($"Could not resolve IP for hostname {hostname}");
            }

            return ipAddress.ToString();
        }

        private static void UpdateVote(NpgsqlConnection connection, string voterId, string vote)
        {
            using (var command = connection.CreateCommand())
            {
                try
                {
                    // Insert new vote
                    command.CommandText = "INSERT INTO votes (id, vote) VALUES (@id, @vote)";
                    command.Parameters.AddWithValue("@id", voterId);
                    command.Parameters.AddWithValue("@vote", vote);
                    command.ExecuteNonQuery();
                }
                catch (DbException)
                {
                    // If vote already exists, update it
                    command.CommandText = "UPDATE votes SET vote = @vote WHERE id = @id";
                    command.ExecuteNonQuery();
                }
            }
        }
    }
}
