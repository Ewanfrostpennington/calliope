from itertools import product

import calliope

__all__ = [
    "inheritance",
    "carrier_validation",
    "not_resource",
    "cost_class_validation",
    "node_coordinate_validation",
    "node_validation",
    "error_if_a_technology_is_defined_twice_in_opposite_directions",
    "export_cost_validation",
    "energy_cap_per_unit",
    "storage_cap_per_unit",
    "finite_forced_resource",
    "gte_storage_discharge_depth",
    "loc_tech_cannot_have_force_resource_and_infinite_resource",
    "ensure_that_if_a_tech_has_negative_costs_there_is_a_max_cap_defined",
    "check_resource_sign",
    "supply_only_allowed_positive_resource",
    "calliope_version_validator",
    "contains_keys",
]


def inheritance(cls, val, values, *, allowed_in):
    # if issubclass(cls, allowed_in):  # FIXME: get the types
    #     raise ValueError(f"{cls} does not inherit from either of {allowed_in}")

    # MRO ends in the base property class, and object, remove those
    if any(
        map(
            lambda i: i[0] in i[1],
            product(allowed_in, map(str, cls.mro()[:-2])),  # FIXME: nasty hack
        )
    ):
        return val
    raise TypeError(f"{cls} does not inherit from either of {allowed_in}")


def carrier_validation(cls, val, values, *, direction):
    defined_carriers = [v for k, v in values.items() if f"_{direction}_" in k]
    if val in defined_carriers:
        return val
    else:
        # raise ValueError(f"Primary carrier {direction} {val} not defined as a carrier for this technology")  # FIXME: do we know what the tech name is?
        raise ValueError(
            f"`{tech}` at `{loc}` is attempting to export a carrier "
            "not given as an output carrier: `{export}`"
        )
        # see checks.py:530


def not_resource(cls, val, values, *, excluded):
    """
    `resource` is special, you can't call a carrier that.
    """
    defined_exclusions = set(val).intersection(excluded)
    if defined_exclusions:
        raise ValueError(
            f"Cannot define the carrier(s) {defined_exclusions} within {cls}"
        )
    return val


def cost_class_validation():
    """
    Look back at config and check that the cost classes defined in the objective
    options match those defined as cost classes in the data.
    NOTE: this should cover all instances of CostClassDict!
    """


def node_coordinate_validation(cls, val, values, *, coordinate_systems):
    """Can only define [x, y] or [lat, lon], no other combination of keys,
    e.g. [x, y, lat, lon], [x, lat]

    """
    # TODO: also validate "all locations must be consistent, all [x, y] or all
    # [lat, lon]" in another validation step
    coordinate_systems = [{"x", "y"}, {"lat", "lon"}]

    coord_sys = set(val.keys())
    if coord_sys in coordinate_systems:
        return val
    else:
        raise ValueError(
            "Incompatible coordinate systems: allowed combinations {x, y} or {lat, lon}"
        )


def node_validation():
    """
    If 'techs' key defined, 'transmission_node' cannot be set to True. Although
    'transmission_node' is somewhat exposing implementation to the user, and
    could possibly be removed entirely
    """


def error_if_a_technology_is_defined_twice_in_opposite_directions():
    """
    What the function name says.
    """


# def objective_options_validation(
#     key: str, keys: Sequence[str], **opts
# ) -> Dict[str, classmethod]:
#     @validator(key, **opts)
#     def _objective_options_validation(cls, _objective, values):
#         """
#         'cost_class' and 'sense' need to be defined if run.objective is 'minmax_cost_optimisation'
#         """
#         if _objective == 'minmax_cost_optimization':
#             if "cost_class" not in values or "sense" not in values:
#                 return ValueError("minmax_cost_optimisation chosen with either cost_class or sense undefined")
#         return _objective

#     return {"objective_options_validation", _objective_options_validation}


def export_cost_validation():
    """
    Can only define an export cost if an export carrier has been defined for the same technology
    """


def energy_cap_per_unit(cls, val, values, /):
    """
    If units are defined, then energy_cap_per_unit must be specified.
    """
    dependent_val = values.get("energy_cap_per_unit", None)
    if dependent_val is not None:
        return val
    else:
        raise ValueError(
            "If units are defined, then energy_cap_per_unit must be specified."
        )


def storage_cap_per_unit(cls, val, values, /):
    """
    If units are defined (and storage is in the inheritance...), then storage_cap_per_unit must be specified.
    """
    dependent_val = values.get("storage_cap_per_unit", None)
    storage_in_hierarchy = False  # TODO: Fixme, is a placeholder now
    if dependent_val is not None and storage_in_hierarchy:
        return val
    else:
        raise ValueError(
            "If units are defined (and storage is in the inheritance...), "
            "then storage_cap_per_unit must be specified."
        )


def finite_forced_resource(cls, val, values, /):
    """
    If a resource value is forced, this value cannot be infinite.
    """
    resource_val = values.get("resource", None)
    if np.isinf(resource_val):
        raise ValueError("Can't be infinte")
    elif isinstance(resource_val, str):
        resource_ts_val = get_timeseries_data(resource_val)
        # TODO: get_timeseries_data should be a key in timeseries_dataframes dictionary
        if resource_ts_val.isinf().any():
            raise ValueError("Can't be infinte")
    else:
        return val


def gte_storage_discharge_depth(cls, val, values, /):
    """
    If defining both `storage_initial` and `storage_discharge_depth`
    then `storage_initial` >= `storage_discharge_depth`
    """
    storage_dod_val = values.get("storage_discharge_depth", 0)
    if val >= storage_dod_val:
        return val
    else:
        raise ValueError(
            """If defining both `storage_initial` and `storage_discharge_depth` then `storage_initial` >= `storage_discharge_depth`"""
        )


##
# Timeseries specific things follow below
##


def loc_tech_cannot_have_force_resource_and_infinite_resource():
    # TODO: Probably not needed, covered by finite_forced_resource
    pass


def ensure_that_if_a_tech_has_negative_costs_there_is_a_max_cap_defined():
    caps = ["energy_cap", "storage_cap", "resource_cap", "resource_area"]
    # if the costs for the above is negative, then ensure there is a *_max
    # if costs.*.$CAPS for $CAPS in caps (list above) is negative, then also
    # constraints.$CAPS_max need to be specified and finite
    costs = ["cost_" + i in model_data.data_vars.keys()]


# for loc_techs_demand see preprocess/checks.py:840
def check_resource_sign(cls, val, values, /):
    resource_ts_val = get_timeseries_data(val)
    # TODO: get_timeseries_data should be a key in timeseries_dataframes dictionary
    # demand is usually time series, but may also be fixed value
    # check if inherits from demand or supply(-like)
    if cls.inherits_from(demand):
        if (resource_ts_val > 0).any():
            raise ValueError(
                "Positive resource given for demand loc_tech {}. All demands "
                "must have negative resource".format(loc_tech)
            )  # FIXME:
    else:  # inherits from supply
        if (resource_ts_val < 0).any():
            raise ValueError(
                "Negative resource given for supply loc_tech {}. All resources "
                "must have positive resource".format(loc_tech)
            )  # FIXME
    return val


# opposite logic as above
def supply_only_allowed_positive_resource():
    pass


def calliope_version_validator(cls, val, values, /):
    if calliope.__version__ != val:
        # currently raises a model warning, meaning you can still run, retain the behaviour
        # unit tests often check for specific errors/warnings, ensure error message doesn't change
        raise ValueError(
            f"Model configuration specifies calliope_version={val}, "
            f"but you are running {calliope.__version__}. Proceed with caution!"
        )
    return val


# this is a root validator to be applied at the technology definition level
def contains_keys(cls, val, *, desired_keys):
    # TODO: get techs with storage, assume it is in the following variable
    # tech_w_storage = ("supply_plus", ) # defined in calliope.preprocess.sets.loc_techs_store
    # if issubclass(cls, tech_w_storage):
    all_keys = set(val.keys())
    if any(i in desired_keys for i in all_keys):
        return val
    else:
        # change to log, current implementation doesn't throw error
        # loc + tech are part of the val name, so extract & split to match msg below
        raise ValueError(
            f"`{tech}` at `{loc}` has no constraint to explicitly connect `energy_cap` to "
            "`storage_cap`, consider defining a `energy_cap_per_storage_cap_min/max/equals` "
            "constraint"
        )
