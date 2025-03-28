import java.util.HashMap;
import java.util.Map;

class Server {
    String name;
    int activeConnections;

    public Server(String name) {
        this.name = name;
        this.activeConnections = 0;
    }

    public void incrementConnections() {
        activeConnections++;
    }

    public void decrementConnections() {
        activeConnections--;
    }

    public int getActiveConnections() {
        return activeConnections;
    }

    public String getName() {
        return name;
    }
}

class LeastConnectionLoadBalancer {
    private Map<String, Server> servers;

    public LeastConnectionLoadBalancer() {
        this.servers = new HashMap<>();
    }

    public void addServer(String serverName) {
        servers.put(serverName, new Server(serverName));
    }

    public Server getServerWithLeastConnections() {
        Server selectedServer = null;
        int minConnections = Integer.MAX_VALUE;

        for (Server server : servers.values()) {
            if (server.getActiveConnections() < minConnections) {
                minConnections = server.getActiveConnections();
                selectedServer = server;
            }
        }

        if (selectedServer != null) {
            selectedServer.incrementConnections();
        }

        return selectedServer;
    }

    public void releaseConnection(Server server) {
        server.decrementConnections();
    }
}

public class LoadBalancerExample {
    public static void main(String[] args) {
        LeastConnectionLoadBalancer loadBalancer = new LeastConnectionLoadBalancer();

        // Add servers to the load balancer
        loadBalancer.addServer("Server1");
        loadBalancer.addServer("Server2");
        loadBalancer.addServer("Server3");

        // Simulate requests and print the server to which each request is routed
        for (int i = 0; i < 10; i++) {
            Server selectedServer = loadBalancer.getServerWithLeastConnections();
            System.out.println("Request " + (i + 1) + ": Routed to " + selectedServer.getName());
            // Simulate releasing the connection after handling the request
            loadBalancer.releaseConnection(selectedServer);
        }
    }
}