import octobot.logger as octobot_logger
import octobot.cli as cli
import octobot_commons.errors as errors
import octobot.configuration_manager as configuration_manager
import octobot.octobot_backtesting_factory as octobot_backtesting
import octobot_commons.constants as common_constants
import octobot_backtesting.constants as backtesting_constants
import octobot.community as octobot_community
import octobot.commands as commands
import octobot
import os
import sys
import octobot_tentacles_manager.api as tentacles_manager_api
import octobot_tentacles_manager.constants as tentacles_manager_constants
from tentacles.Evaluator.Strategies.historian.historian import HISTORY_BOOK
import time
import json


def _load_or_create_tentacles(config, logger):
    # add tentacles folder to Python path
    sys.path.append(os.path.realpath(os.getcwd()))

    # when tentacles folder already exists
    if os.path.isfile(tentacles_manager_constants.USER_REFERENCE_TENTACLE_CONFIG_FILE_PATH):
        config.load_profiles_if_possible_and_necessary()
        tentacles_setup_config = tentacles_manager_api.get_tentacles_setup_config(
            config.get_tentacles_config_path()
        )
        commands.run_update_or_repair_tentacles_if_necessary(config, tentacles_setup_config)
    else:
        # when no tentacles folder has been found
        logger.info("OctoBot tentacles can't be found. Installing default tentacles ...")
        commands.run_tentacles_install_or_update(config)
        config.load_profiles_if_possible_and_necessary()

def wait_for():
    bot.task_manager.loop_forever_thread.join()
    json.dump(HISTORY_BOOK, open('/tmp/history_book.json', 'w+'))
    logger.error("Stored history book: /tmp/history_book.json")


if __name__ == '__main__':
    logger = octobot_logger.init_logger()
    cli._log_environment(logger)
    config = cli._create_startup_config(logger)

    # show terms
    cli._log_terms_if_unaccepted(config, logger)

    # switch environments if necessary
    octobot_community.IdentifiersProvider.use_environment_from_config(config)

    # check config loading
    if not config.is_loaded():
        raise errors.ConfigError

    config.config[backtesting_constants.CONFIG_BACKTESTING][
       backtesting_constants.CONFIG_BACKTESTING_DATA_FILES] = ['ExchangeHistoryDataCollector_1667992411.4607506.data']
    config.config[backtesting_constants.CONFIG_BACKTESTING][common_constants.CONFIG_ENABLED_OPTION] = True
    config.config[common_constants.CONFIG_TRADER][common_constants.CONFIG_ENABLED_OPTION] = False
    config.config[common_constants.CONFIG_SIMULATOR][common_constants.CONFIG_ENABLED_OPTION] = True
    print(config.config)
    
    # tries to load, install or repair tentacles
    _load_or_create_tentacles(config, logger)
    # Can now perform config health check (some checks require a loaded profile)
    configuration_manager.config_health_check(config, True)

    logger.info(f"Config {config}")
    bot = octobot_backtesting.OctoBotBacktestingFactory(config,
                                                        run_on_common_part_only=False,
                                                        enable_join_timeout=False,
                                                        enable_logs=True)
    # In those cases load OctoBot
    cli._disable_interface_from_param("telegram", True, logger)
    cli._disable_interface_from_param("web", True, logger)
    octobot.set_bot(bot)
    # Clear community cache
    bot.community_auth.clear_cache()
    
    commands.run_bot(bot, logger)
    while bot.independent_backtesting is None:
        print(".")
        time.sleep(10)
    wait_for()
