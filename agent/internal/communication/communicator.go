package communication

import (
	"encoding/json"
	"fmt"

	"github.com/nats-io/nats.go"
	"go.uber.org/zap"
)

// Communicator handles communication with the RMM server
type Communicator struct {
	serverURL string
	agentID   string
	conn      *nats.Conn
	logger    *zap.Logger
}

// NewCommunicator creates a new communicator instance
func NewCommunicator(serverURL, agentID string, logger *zap.Logger) (*Communicator, error) {
	// Connect to NATS server
	natsURL := serverURL + ":4222" // TODO: Parse proper NATS URL
	conn, err := nats.Connect(natsURL,
		nats.Name(agentID),
		nats.MaxReconnects(-1),
		nats.DisconnectErrHandler(func(nc *nats.Conn, err error) {
			logger.Warn("NATS disconnected", zap.Error(err))
		}),
		nats.ReconnectHandler(func(nc *nats.Conn) {
			logger.Info("NATS reconnected")
		}),
	)

	if err != nil {
		return nil, fmt.Errorf("failed to connect to NATS: %w", err)
	}

	logger.Info("Connected to NATS", zap.String("url", natsURL))

	c := &Communicator{
		serverURL: serverURL,
		agentID:   agentID,
		conn:      conn,
		logger:    logger,
	}

	// Subscribe to commands
	go c.subscribeToCommands()

	return c, nil
}

// SendHeartbeat sends a heartbeat to the server
func (c *Communicator) SendHeartbeat() error {
	data := map[string]interface{}{
		"agent_id":  c.agentID,
		"timestamp": 	"timestamp": fmt.Sprintf("%d", time.Now().Unix()),
	}

	return c.publish(fmt.Sprintf("agent.%s.heartbeat", c.agentID), data)
}

// SendMetrics sends system metrics to the server
func (c *Communicator) SendMetrics(metrics interface{}) error {
	return c.publish(fmt.Sprintf("agent.%s.metrics", c.agentID), metrics)
}

// SendLog sends a log message to the server
func (c *Communicator) SendLog(level, message string) error {
	data := map[string]interface{}{
		"agent_id": c.agentID,
		"level":    level,
		"message":  message,
	}

	return c.publish(fmt.Sprintf("agent.%s.log", c.agentID), data)
}

// subscribeToCommands subscribes to command messages from server
func (c *Communicator) subscribeToCommands() {
	subject := fmt.Sprintf("agent.%s.command", c.agentID)

	_, err := c.conn.Subscribe(subject, func(msg *nats.Msg) {
		c.logger.Info("Received command", zap.String("subject", msg.Subject))

		var cmd map[string]interface{}
		if err := json.Unmarshal(msg.Data, &cmd); err != nil {
			c.logger.Error("Failed to parse command", zap.Error(err))
			return
		}

		// Handle command
		c.handleCommand(cmd)
	})

	if err != nil {
		c.logger.Error("Failed to subscribe to commands", zap.Error(err))
	} else {
		c.logger.Info("Subscribed to commands", zap.String("subject", subject))
	}
}

// handleCommand processes commands from the server
func (c *Communicator) handleCommand(cmd map[string]interface{}) {
	cmdType, ok := cmd["type"].(string)
	if !ok {
		c.logger.Error("Invalid command type")
		return
	}

	c.logger.Info("Handling command", zap.String("type", cmdType))

	// TODO: Implement command handlers
	switch cmdType {
	case "execute":
		// Execute script/command
	case "update":
		// Update software/OS
	case "reboot":
		// Reboot system
	default:
		c.logger.Warn("Unknown command type", zap.String("type", cmdType))
	}
}

// publish sends a message to NATS
func (c *Communicator) publish(subject string, data interface{}) error {
	payload, err := json.Marshal(data)
	if err != nil {
		return fmt.Errorf("failed to marshal data: %w", err)
	}

	if err := c.conn.Publish(subject, payload); err != nil {
		return fmt.Errorf("failed to publish message: %w", err)
	}

	return nil
}

// Close closes the NATS connection
func (c *Communicator) Close() {
	if c.conn != nil {
		c.conn.Close()
		c.logger.Info("NATS connection closed")
	}
}
