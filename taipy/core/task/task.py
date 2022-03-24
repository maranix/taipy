import uuid
from typing import Dict, Iterable, Optional

from taipy.core.common._entity import _Entity
from taipy.core.common._reload import _self_reload, _self_setter
from taipy.core.common._validate_id import _validate_id
from taipy.core.common.alias import TaskId
from taipy.core.data.data_node import DataNode
from taipy.core.data.scope import Scope


class Task(_Entity):
    """
    Holds a user function that will be executed, its parameters and the results.

    The `Task^` brings together the user code as function, the inputs and the outputs as data nodes (instances
    of `DataNode^` class).

    Attributes:
        config_id (str): The identifier of the `TaskConfig^`.
        function (callable): The python function to execute. The _function_ must take as parameter the
            data referenced by inputs data nodes, and must return the data referenced by outputs data nodes.
        input (`DataNode^` or List[`DataNode^`]): The list of `DataNode^` inputs.
        output (`DataNode^` or List[`DataNode^`]): The list of `DataNode^` outputs.
        id (str): The unique identifier of the task.
        parent_id (str):  The identifier of the parent (pipeline_id, scenario_id, cycle_id) or `None`.
    """

    _ID_PREFIX = "TASK"
    __ID_SEPARATOR = "_"
    _MANAGER_NAME = "task"

    def __init__(
        self,
        config_id: str,
        function,
        input: Optional[Iterable[DataNode]] = None,
        output: Optional[Iterable[DataNode]] = None,
        id: TaskId = None,
        parent_id: Optional[str] = None,
    ):
        self.config_id = _validate_id(config_id)
        self.id = id or TaskId(self.__ID_SEPARATOR.join([self._ID_PREFIX, self.config_id, str(uuid.uuid4())]))
        self.parent_id = parent_id
        self.__input = {dn.config_id: dn for dn in input or []}
        self.__output = {dn.config_id: dn for dn in output or []}
        self._function = function

    def __hash__(self):
        return hash(self.id)

    def __getstate__(self):
        return vars(self)

    def __setstate__(self, state):
        vars(self).update(state)

    @property  # type: ignore
    def input(self) -> Dict[str, DataNode]:
        return self.__input

    @property  # type: ignore
    def output(self) -> Dict[str, DataNode]:
        return self.__output

    @property  # type: ignore
    def data_nodes(self) -> Dict[str, DataNode]:
        return {**self.input, **self.output}

    @property  # type: ignore
    @_self_reload(_MANAGER_NAME)
    def function(self):
        return self._function

    @function.setter  # type: ignore
    @_self_setter(_MANAGER_NAME)
    def function(self, val):
        self._function = val

    def __getattr__(self, attribute_name):
        protected_attribute_name = _validate_id(attribute_name)
        if protected_attribute_name in self.input:
            return self.input[protected_attribute_name]
        if protected_attribute_name in self.output:
            return self.output[protected_attribute_name]
        raise AttributeError(f"{attribute_name} is not an attribute of task {self.id}")

    @property
    def scope(self) -> Scope:
        """Retrieve the lowest scope of the task based on its data nodes.

        Returns:
           Lowest `Scope^` present in input and output data nodes or GLOBAL if there are either no input or no output.
        """
        data_nodes = list(self.__input.values()) + list(self.__output.values())
        scope = min(dn.scope for dn in data_nodes) if len(data_nodes) != 0 else Scope.GLOBAL
        return Scope(scope)
