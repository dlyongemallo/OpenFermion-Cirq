# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Subclasses of abstract classes for use in tests."""

from typing import Optional, Sequence, Union, cast

import numpy

import cirq

from openfermioncirq.optimization.algorithm import OptimizationAlgorithm
from openfermioncirq.optimization.black_box import BlackBox, StatefulBlackBox
from openfermioncirq.optimization.result import OptimizationResult
from openfermioncirq.variational.ansatz import VariationalAnsatz
from openfermioncirq.variational.study import VariationalStudy


class ExampleAlgorithm(OptimizationAlgorithm):
    """Evaluates 5 random points and returns the best answer found."""

    def optimize(self,
                 black_box: BlackBox,
                 initial_guess: Optional[numpy.ndarray]=None,
                 initial_guess_array: Optional[numpy.ndarray]=None
                 ) -> OptimizationResult:
        opt = numpy.inf
        opt_params = None
        for _ in range(5):
            guess = numpy.random.randn(black_box.dimension)
            val = black_box.evaluate(guess)
            if val < opt:
                opt = val
                opt_params = guess
        return OptimizationResult(
                optimal_value=opt,
                optimal_parameters=cast(numpy.ndarray, opt_params),
                num_evaluations=1,
                cost_spent=0.0,
                status=0,
                message='success')


class ExampleBlackBox(BlackBox):
    """Returns the sum of the squares of the inputs."""

    @property
    def dimension(self) -> int:
        return 2

    def evaluate(self,
                 x: numpy.ndarray) -> float:
        return numpy.sum(x**2)


class ExampleBlackBoxNoisy(ExampleBlackBox):
    """Returns the sum of the squares of the inputs plus some noise.

    The noise is drawn from the standard normal distribution, then divided
    by the cost provided.
    """

    def evaluate_with_cost(self,
                           x: numpy.ndarray,
                           cost: float) -> float:
        return numpy.sum(x**2) + numpy.random.randn() / cost


class ExampleStatefulBlackBox(StatefulBlackBox):
    """Returns the sum of the squares of the inputs."""

    @property
    def dimension(self) -> int:
        return 2  # coverage: ignore

    def _evaluate(self,
                  x: numpy.ndarray) -> float:
        return numpy.sum(x**2)


class ExampleAnsatz(VariationalAnsatz):
    """An example variational ansatz.

    The ansatz produces the operations::

        0: ───X^theta0───@───X^theta0───M('all')───
                         │              │
        1: ───X^theta1───@───X^theta1───M──────────
    """

    def param_names(self) -> Sequence[str]:
        return ['theta{}'.format(i) for i in range(2)]

    def _generate_qubits(self) -> Sequence[cirq.QubitId]:
        return cirq.LineQubit.range(2)

    def operations(self, qubits: Sequence[cirq.QubitId]) -> cirq.OP_TREE:
        a, b = qubits
        yield cirq.RotXGate(half_turns=self.params['theta0']).on(a)
        yield cirq.RotXGate(half_turns=self.params['theta1']).on(b)
        yield cirq.CZ(a, b)
        yield cirq.RotXGate(half_turns=self.params['theta0']).on(a)
        yield cirq.RotXGate(half_turns=self.params['theta1']).on(b)
        yield cirq.MeasurementGate('all').on(a, b)


class ExampleStudy(VariationalStudy):
    """An example variational study.

    The value of the study is the number of qubits that were measured to be 1.
    """

    def value(self,
              trial_result: Union[cirq.TrialResult,
                                  cirq.google.XmonSimulateTrialResult]
              ) -> float:
        measurements = trial_result.measurements['all']
        return numpy.sum(measurements)


class ExampleStudyNoisy(ExampleStudy):
    """An example study with a noise model.

    The noise is drawn from the standard normal distribution, then divided
    by the cost provided. If a cost is not specified, the noise is 0.
    """

    def noise(self, cost: Optional[float]=None) -> float:
        if cost is None:
            return 0.0  # coverage: ignore
        return numpy.random.randn() / cost
