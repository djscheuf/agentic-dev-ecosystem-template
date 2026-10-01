# Go: Testing, Replay, and Shadowing

Cadence gives you three complementary tools: **unit testing** (fast, isolated, in-process),
**Workflow Replayer** (verify a code change against real recorded history), and **Workflow Shadower**
(replay many production histories continuously to catch incompatible changes before they bite).

## Unit testing

```go
package sample

import (
    "errors"
    "testing"

    "github.com/stretchr/testify/mock"
    "github.com/stretchr/testify/suite"

    "go.uber.org/cadence"
    "go.uber.org/cadence/testsuite"
)

type UnitTestSuite struct {
    suite.Suite
    testsuite.WorkflowTestSuite

    env *testsuite.TestWorkflowEnvironment
}

func (s *UnitTestSuite) SetupTest() {
    s.env = s.NewTestWorkflowEnvironment()
}

func (s *UnitTestSuite) AfterTest(suiteName, testName string) {
    s.env.AssertExpectations(s.T())
}

func (s *UnitTestSuite) Test_SimpleWorkflow_Success() {
    s.env.ExecuteWorkflow(SimpleWorkflow, "test_success")

    s.True(s.env.IsWorkflowCompleted())
    s.NoError(s.env.GetWorkflowError())
}

func TestUnitTestSuite(t *testing.T) {
    suite.Run(t, new(UnitTestSuite))
}
```

- `s.env.ExecuteWorkflow(...)` runs the workflow (and any activities it invokes) **in-process**,
  synchronously from the test's perspective — Cadence's test framework uses an internal clock so
  `workflow.Sleep(ctx, 10*time.Minute)` doesn't actually block the test for 10 minutes.
- Unless mocked/overridden, activities run their **real** implementation, including real outbound
  calls — mock them if that's not what you want.
- After execution, assert with `s.env.IsWorkflowCompleted()`, `s.env.GetWorkflowError()`, and
  `s.env.GetWorkflowResult(&value)`.

### Mocking / overriding activities

```go
func (s *UnitTestSuite) Test_SimpleWorkflow_ActivityFails() {
    s.env.OnActivity(SimpleActivity, mock.Anything, mock.Anything).Return(
        "", errors.New("SimpleActivityFailure"))
    s.env.ExecuteWorkflow(SimpleWorkflow, "test_failure")

    s.True(s.env.IsWorkflowCompleted())
    s.NotNil(s.env.GetWorkflowError())
    s.True(cadence.IsGenericError(s.env.GetWorkflowError()))
    s.Equal("SimpleActivityFailure", s.env.GetWorkflowError().Error())
}
```

Pass a function to `.Return(...)` instead of a fixed value/error to substitute a full alternate
implementation (useful for asserting on the exact arguments the workflow passed in):

```go
s.env.OnActivity(SimpleActivity, mock.Anything, mock.Anything).Return(
    func(ctx context.Context, value string) (string, error) {
        s.Equal("test_success", value)
        return value, nil
    },
)
```

The framework validates that the mock function's signature matches the real activity's signature.

### Testing signals

Register the signal delivery via `RegisterDelayedCallback` **before** calling `ExecuteWorkflow`, or
the signal won't be delivered:

```go
func (s *UnitTestSuite) Test_SimpleWorkflow_Signal() {
    s.env.RegisterDelayedCallback(func() {
        s.env.SignalWorkflow(signalName, signalData)
    }, time.Minute*10)

    s.env.ExecuteWorkflow(SimpleWorkflow, "test_success")

    s.True(s.env.IsWorkflowCompleted())
    s.NoError(s.env.GetWorkflowError())
}
```

The "10 minutes" delay is virtual — the test's internal clock fast-forwards to the next scheduled
event rather than actually sleeping.

## Workflow Replayer

Even a passing unit test suite can't catch every accidental non-determinism bug (see
[control-flow.md](control-flow.md#versioning-workflowgetversion) and
[../06-debugging/non-deterministic-errors.md](../06-debugging/non-deterministic-errors.md)). The
**Workflow Replayer** re-runs your *current* workflow code against a *real, previously-recorded*
Event History, using the exact same replay logic Cadence uses in production — if your code change is
incompatible, the replay fails immediately, in a fast local test.

```go
func TestReplayWorkflowHistoryFromFile(t *testing.T) {
    replayer := worker.NewWorkflowReplayer()
    replayer.RegisterWorkflow(helloWorldWorkflow)
    err := replayer.ReplayWorkflowHistoryFromJSONFile(zaptest.NewLogger(t), "helloworld.json")
    require.NoError(t, err)
}
```

**Get a history file to replay against:**

```bash
cadence --do <domain> workflow show --wid <workflowID> --rid <runID> --of history.json
```

Key replay APIs:
- `ReplayWorkflowHistoryFromJSONFile(logger, path)` — from a file produced by `workflow show --of`.
- `ReplayPartialWorkflowHistoryFromJSONFile(logger, path, eventID)` — replay only up to a given
  decision-task event, useful to isolate exactly where a change becomes incompatible.
- `ReplayWorkflowExecution(ctx, serviceClient, logger, domain, execution)` — fetch and replay
  directly against a live server, no intermediate file.

**Important:** replayer options and registration must exactly match what your production worker
used (same `DataConverter`, `ContextPropagators`, registered workflow names) or you'll get false
replay failures. Minimum 3 history events required for a meaningful replay.

## Workflow Shadower

Replayer doesn't scale to "verify against every production workflow." **Workflow Shadower** builds on
Replayer: it scans workflows matching a filter, fetches each one's history from the server, and
replays it — either as a one-off local test or as a continuously-running worker process.

```go
func TestShadowWorkflow(t *testing.T) {
    options := worker.ShadowOptions{
        WorkflowStartTimeFilter: worker.TimeFilter{MinTimestamp: time.Now().Add(-time.Hour)},
        ExitCondition:           worker.ShadowExitCondition{ShadowCount: 10},
    }
    service := buildCadenceClient() // see ../02-go-client/workflows-and-workers.md
    shadower, err := worker.NewWorkflowShadower(service, "samples-domain", options, worker.ReplayOptions{}, zaptest.NewLogger(t))
    require.NoError(t, err)

    shadower.RegisterWorkflowWithOptions(helloWorldWorkflow, workflow.RegisterOptions{Name: "helloWorld"})
    require.NoError(t, shadower.Run())
}
```

Key option groups:
- **Scan filter**: either `WorkflowQuery` (advanced visibility syntax) OR the basic trio
  `WorkflowTypes` / `WorkflowStatus` / `WorkflowStartTimeFilter` (not both). `SamplingRate` works
  with either. By default, an empty status filter scans only `OPEN` workflows.
- **Exit condition**: `ExpirationInterval` (time-boxed) or `ShadowCount` (replay N workflows, not
  counting skips due to fetch errors/too-short history).
- **Mode**: `Normal` (one pass) or `Continuous` (repeats every 5 minutes until `ExitCondition`, which
  is then required).
- **Concurrency**: default 1; higher only takes effect when run as a **Shadowing Worker**.

### Running as a continuous Shadowing Worker (not just a local test)

- Each domain is limited to **one** Shadowing Worker.
- It runs as a single shadowing workflow inside the special `cadence-shadower` domain — create that
  domain first.
- It scans/fetches history from the same Cadence server it's shadowing against (no cross-server
  shadowing today).

For a guided walkthrough, see the official
[Workflow Testing Codelab](https://cadenceworkflow.io/docs/codelabs/workflow-tests-go-replayer-shadower)
(Replayer setup, Shadower integration, breaking-change detection; ~30-45 min).
