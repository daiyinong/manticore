from .detectors import (
    DetectInvalid,
    DetectIntegerOverflow,
    DetectUninitializedStorage,
    DetectUninitializedMemory,
    DetectReentrancySimple,
    DetectReentrancyAdvanced,
    DetectUnusedRetVal,
    DetectSuicidal,
    DetectDelegatecall,
    DetectExternalCallAndLeak,
    DetectEnvInstruction,
    DetectRaceCondition,
    DetectorClassification,
)
from ..core.plugin import Profiler
from .manticore import ManticoreEVM
from .plugins import FilterFunctions, LoopDepthLimiter, VerboseTrace
from ..utils.nointerrupt import WithKeyboardInterruptAs
from ..utils import config

consts = config.get_group("cli")
consts.add("profile", default=False, description="Enable worker profiling mode")


def get_detectors_classes():
    return [
        DetectInvalid,
        DetectIntegerOverflow,
        DetectUninitializedStorage,
        DetectUninitializedMemory,
        DetectReentrancySimple,
        DetectReentrancyAdvanced,
        DetectUnusedRetVal,
        DetectSuicidal,
        DetectDelegatecall,
        DetectExternalCallAndLeak,
        DetectEnvInstruction,
        # The RaceCondition detector has been disabled for now as it seems to collide with IntegerOverflow detector
        # DetectRaceCondition
    ]


def choose_detectors(args):
    all_detector_classes = get_detectors_classes()
    detectors = {d.ARGUMENT: d for d in all_detector_classes}
    arguments = list(detectors.keys())

    detectors_to_run = []

    if not args.exclude_all:
        exclude = []

        if args.detectors_to_exclude:
            exclude = args.detectors_to_exclude.split(",")

            for e in exclude:
                if e not in arguments:
                    raise Exception(
                        f"{e} is not a detector name, must be one of {arguments}. See also `--list-detectors`."
                    )

        for arg, detector_cls in detectors.items():
            if arg not in exclude:
                detectors_to_run.append(detector_cls)

    return detectors_to_run


def ethereum_main(args, logger):
    policy = args.policy
    m = ManticoreEVM(workspace_url=args.workspace, policy=policy)
    with WithKeyboardInterruptAs(m.kill):

        if args.verbose_trace:
            m.register_plugin(VerboseTrace())

        if args.limit_loops:
            m.register_plugin(LoopDepthLimiter())

        for detector in choose_detectors(args):
            m.register_detector(detector())

        if consts.profile:
            profiler = Profiler()
            m.register_plugin(profiler)

        if args.avoid_constant:
            # avoid all human level tx that has no effect on the storage
            filter_nohuman_constants = FilterFunctions(
                regexp=r".*", depth="human", mutability="constant", include=False
            )
            m.register_plugin(filter_nohuman_constants)

        if m.plugins:
            logger.info(f'Registered plugins: {", ".join(d.name for d in m.plugins)}')

        logger.info("Beginning analysis")

        rl_mode = False

        if policy == "rl":
            rl_mode = True
            max_iterations = 20
        if not rl_mode:
            with m.kill_timeout():
                m.multi_tx_analysis(
                    args.argv[0],
                    contract_name=args.contract,
                    tx_limit=args.txlimit,
                    tx_use_coverage=not args.txnocoverage,
                    tx_send_ether=not args.txnoether,
                    tx_account=args.txaccount,
                    tx_preconstrain=args.txpreconstrain,
                )
        else:
            for i in range(max_iterations):
                logger.info("iteration %d" % (i + 1))
                m.multi_tx_analysis(
                    args.argv[0],
                    contract_name=args.contract,
                    tx_limit=args.txlimit,
                    tx_use_coverage=not args.txnocoverage,
                    tx_send_ether=not args.txnoether,
                    tx_account=args.txaccount,
                    tx_preconstrain=args.txpreconstrain,
                )
                branch_dict = m._shared_context["branch_dict"]
                gas_dict = m._shared_context["gas_dict"]
                policy_dict = process_policy(branch_dict, gas_dict)
                if i != max_iterations - 1:
                    m = ManticoreEVM(workspace_url=args.workspace, policy=policy, policy_dict=policy_dict)

        if not args.no_testcases:
            m.finalize()
        else:
            m.kill()

        if consts.profile:
            with open("profiling.bin", "wb") as f:
                profiler.save_profiling_data(f)

        for detector in list(m.detectors):
            m.unregister_detector(detector)

        for plugin in list(m.plugins):
            m.unregister_plugin(plugin)

def process_policy(branch_dict, gas_dict):
    result_dict = dict()
    for (key, value) in branch_dict.items():
        if value in gas_dict:
            result_dict[key] = gas_dict[value]
        else:
            result_dict[key] = 0.0
    return result_dict
