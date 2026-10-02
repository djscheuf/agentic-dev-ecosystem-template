// Unit test for HelloWorldWorkflow using the Cadence test framework.
// See ../../02-go-client/testing-and-replay.md for the full explanation of this pattern
// (mocking activities, testing signals, and Workflow Replayer/Shadower for compatibility testing).
package helloworld

import (
	"testing"

	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/suite"
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

func (s *UnitTestSuite) Test_HelloWorldWorkflow_Success() {
	s.env.ExecuteWorkflow(HelloWorldWorkflow, "World")

	s.True(s.env.IsWorkflowCompleted())
	s.NoError(s.env.GetWorkflowError())

	var result string
	s.NoError(s.env.GetWorkflowResult(&result))
	s.Equal("Hello World!", result)
}

func (s *UnitTestSuite) Test_HelloWorldWorkflow_ActivityFails() {
	s.env.OnActivity(HelloWorldActivity, mock.Anything, mock.Anything).Return(
		"", assertNewError("boom"))

	s.env.ExecuteWorkflow(HelloWorldWorkflow, "World")

	s.True(s.env.IsWorkflowCompleted())
	s.Error(s.env.GetWorkflowError())
}

func assertNewError(msg string) error {
	return &testError{msg}
}

type testError struct{ msg string }

func (e *testError) Error() string { return e.msg }

func TestUnitTestSuite(t *testing.T) {
	suite.Run(t, new(UnitTestSuite))
}
