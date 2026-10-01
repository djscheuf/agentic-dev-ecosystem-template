// Minimal gRPC-based Cadence worker for local development.
// Registers workflows/activities from hello_world_workflow.go and starts polling.
// See ../../02-go-client/workflows-and-workers.md#worker-service for the full explanation,
// and ../../04-configuration/client-connection.md for tchannel/TLS alternatives.
package main

import (
	"go.uber.org/cadence/.gen/go/cadence/workflowserviceclient"
	"go.uber.org/cadence/compatibility"
	"go.uber.org/cadence/worker"

	apiv1 "github.com/cadence-workflow/cadence-idl/go/proto/api/v1"
	"github.com/uber-go/tally"
	"go.uber.org/yarpc"
	"go.uber.org/yarpc/transport/grpc"
	"go.uber.org/zap"
)

const (
	HostPort       = "127.0.0.1:7833" // gRPC frontend port for the local SQLite quickstart
	Domain         = "test-domain"
	TaskListName   = "hello-world-tasklist"
	ClientName     = "hello-world-worker"
	CadenceService = "cadence-frontend"
)

func main() {
	logger, _ := zap.NewDevelopment()

	serviceClient := buildCadenceClient()

	workerOptions := worker.Options{
		Logger:       logger,
		MetricsScope: tally.NewTestScope(TaskListName, map[string]string{}),
	}
	w := worker.New(serviceClient, Domain, TaskListName, workerOptions)

	if err := w.Start(); err != nil {
		logger.Fatal("failed to start worker", zap.Error(err))
	}
	logger.Info("worker started, polling task list", zap.String("taskList", TaskListName))

	select {} // block forever; Ctrl-C to stop
}

func buildCadenceClient() workflowserviceclient.Interface {
	dispatcher := yarpc.NewDispatcher(yarpc.Config{
		Name: ClientName,
		Outbounds: yarpc.Outbounds{
			CadenceService: {Unary: grpc.NewTransport().NewSingleOutbound(HostPort)},
		},
	})
	if err := dispatcher.Start(); err != nil {
		panic(err)
	}
	clientConfig := dispatcher.ClientConfig(CadenceService)
	return compatibility.NewThrift2ProtoAdapter(
		apiv1.NewDomainAPIYARPCClient(clientConfig),
		apiv1.NewWorkflowAPIYARPCClient(clientConfig),
		apiv1.NewWorkerAPIYARPCClient(clientConfig),
		apiv1.NewVisibilityAPIYARPCClient(clientConfig),
	)
}
