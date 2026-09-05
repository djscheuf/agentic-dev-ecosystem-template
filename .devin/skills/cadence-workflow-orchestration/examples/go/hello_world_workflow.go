// Minimal hello-world Cadence workflow + activity for Go.
// See ../../00-get-started/local-quickstart.md for how to run a local server and domain,
// and ../../02-go-client/workflows-and-workers.md for the full explanation of every piece here.
package helloworld

import (
	"context"
	"time"

	"go.uber.org/cadence/activity"
	"go.uber.org/cadence/workflow"
)

func init() {
	workflow.Register(HelloWorldWorkflow)
	activity.Register(HelloWorldActivity)
}

// HelloWorldWorkflow orchestrates a single activity call.
func HelloWorldWorkflow(ctx workflow.Context, name string) (string, error) {
	ao := workflow.ActivityOptions{
		ScheduleToStartTimeout: time.Minute,
		StartToCloseTimeout:    time.Minute,
		HeartbeatTimeout:       time.Second * 20,
	}
	ctx = workflow.WithActivityOptions(ctx, ao)

	logger := workflow.GetLogger(ctx)
	logger.Info("HelloWorldWorkflow started")

	var result string
	err := workflow.ExecuteActivity(ctx, HelloWorldActivity, name).Get(ctx, &result)
	if err != nil {
		logger.Error("Activity failed.")
		return "", err
	}

	logger.Info("HelloWorldWorkflow completed")
	return result, nil
}

// HelloWorldActivity performs the actual (non-deterministic-safe) work.
func HelloWorldActivity(ctx context.Context, name string) (string, error) {
	activity.GetLogger(ctx).Info("HelloWorldActivity called")
	return "Hello " + name + "!", nil
}
