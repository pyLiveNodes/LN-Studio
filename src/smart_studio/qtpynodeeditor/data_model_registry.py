import logging
from .node_data import NodeDataModel

logger = logging.getLogger(__name__)


class DataModelRegistry:
    def __init__(self):
        self._models_category = {}
        self._item_creators = {}
        self._categories = set()

    def register_model(self, creator, category='', *, style=None, **init_kwargs):
        name = creator.name
        self._item_creators[name] = (creator, {'style': style, **init_kwargs})
        self._categories.add(category)
        self._models_category[name] = category

    def create(self, model_name: str) -> NodeDataModel:
        """
        Create a :class:`NodeDataModel` given its user-friendly name.

        Parameters
        ----------
        model_name : str

        Returns
        -------
        data_model_instance : NodeDataModel
            The instance of the given data model.

        Raises
        ------
        ValueError
            If the model name is not registered.
        """
        cls, kwargs = self.get_model_by_name(model_name)
        return cls(**kwargs)

    def get_model_by_name(self, model_name: str
                          ) -> tuple[type[NodeDataModel], dict]:
        """
        Get information on how to create a specific :class:`NodeDataModel`
        node given its user-friendly name.

        Parameters
        ----------
        model_name : str

        Returns
        -------
        data_model : NodeDataModel
            The data model class.

        init_kwargs : dict
            Default init keyword arguments.

        Raises
        ------
        ValueError
            If the model name is not registered.
        """
        try:
            return self._item_creators[model_name]
        except KeyError:
            raise ValueError(f'Unknown model: {model_name}') from None

    def registered_model_creators(self) -> dict:
        """
        Registered model creators

        Returns
        -------
        value : dict
        """
        return dict(self._item_creators)

    def registered_models_category_association(self) -> dict:
        """
        Registered models category association

        Returns
        -------
        value : DataModelRegistry.RegisteredModelsCategoryMap
        """
        return self._models_category

    def categories(self) -> set:
        """
        Categories

        Returns
        -------
        value : DataModelRegistry.CategoriesSet
        """
        return self._categories
