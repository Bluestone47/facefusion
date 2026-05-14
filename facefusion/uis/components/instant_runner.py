import os
from time import sleep
from typing import Optional, Tuple

import gradio

from facefusion import process_manager, state_manager, translator
from facefusion.args import collect_step_args
from facefusion.common_helper import get_first
from facefusion.core import process_step
from facefusion.filesystem import get_file_extension, get_file_name, is_directory, is_file, is_image, is_video
from facefusion.jobs import job_helper, job_manager, job_runner, job_store
from facefusion.temp_helper import clear_temp_directory
from facefusion.types import Args, UiWorkflow
from facefusion.uis.core import get_ui_component

INSTANT_RUNNER_WRAPPER : Optional[gradio.Row] = None
INSTANT_RUNNER_MIDDLE_WRAPPER : Optional[gradio.Row] = None
INSTANT_RUNNER_MIDDLE_START_BUTTON : Optional[gradio.Button] = None
INSTANT_RUNNER_MIDDLE_STOP_BUTTON : Optional[gradio.Button] = None
INSTANT_RUNNER_MIDDLE_CLEAR_BUTTON : Optional[gradio.Button] = None
INSTANT_RUNNER_START_BUTTON : Optional[gradio.Button] = None
INSTANT_RUNNER_STOP_BUTTON : Optional[gradio.Button] = None
INSTANT_RUNNER_CLEAR_BUTTON : Optional[gradio.Button] = None


def render_middle() -> None:
	global INSTANT_RUNNER_MIDDLE_WRAPPER
	global INSTANT_RUNNER_MIDDLE_START_BUTTON
	global INSTANT_RUNNER_MIDDLE_STOP_BUTTON
	global INSTANT_RUNNER_MIDDLE_CLEAR_BUTTON

	if job_manager.init_jobs(state_manager.get_item('jobs_path')):
		is_instant_runner = state_manager.get_item('ui_workflow') == 'instant_runner'

		with gradio.Row(visible = is_instant_runner) as INSTANT_RUNNER_MIDDLE_WRAPPER:
			INSTANT_RUNNER_MIDDLE_START_BUTTON = gradio.Button(
				value = translator.get('uis.start_button'),
				variant = 'primary',
				size = 'sm'
			)
			INSTANT_RUNNER_MIDDLE_STOP_BUTTON = gradio.Button(
				value = translator.get('uis.stop_button'),
				variant = 'primary',
				size = 'sm',
				visible = False
			)
			INSTANT_RUNNER_MIDDLE_CLEAR_BUTTON = gradio.Button(
				value = translator.get('uis.clear_button'),
				size = 'sm'
			)


def render() -> None:
	global INSTANT_RUNNER_WRAPPER
	global INSTANT_RUNNER_START_BUTTON
	global INSTANT_RUNNER_STOP_BUTTON
	global INSTANT_RUNNER_CLEAR_BUTTON

	if job_manager.init_jobs(state_manager.get_item('jobs_path')):
		is_instant_runner = state_manager.get_item('ui_workflow') == 'instant_runner'

		with gradio.Row(visible = is_instant_runner) as INSTANT_RUNNER_WRAPPER:
			INSTANT_RUNNER_START_BUTTON = gradio.Button(
				value = translator.get('uis.start_button'),
				variant = 'primary',
				size = 'sm'
			)
			INSTANT_RUNNER_STOP_BUTTON = gradio.Button(
				value = translator.get('uis.stop_button'),
				variant = 'primary',
				size = 'sm',
				visible = False
			)
			INSTANT_RUNNER_CLEAR_BUTTON = gradio.Button(
				value = translator.get('uis.clear_button'),
				size = 'sm'
			)


def listen() -> None:
	output_image = get_ui_component('output_image')
	output_video = get_ui_component('output_video')
	ui_workflow_dropdown = get_ui_component('ui_workflow_dropdown')

	if output_image and output_video:
		start_outputs = [ INSTANT_RUNNER_START_BUTTON, INSTANT_RUNNER_STOP_BUTTON, INSTANT_RUNNER_MIDDLE_START_BUTTON, INSTANT_RUNNER_MIDDLE_STOP_BUTTON ]
		run_outputs = [ INSTANT_RUNNER_START_BUTTON, INSTANT_RUNNER_STOP_BUTTON, INSTANT_RUNNER_MIDDLE_START_BUTTON, INSTANT_RUNNER_MIDDLE_STOP_BUTTON, output_image, output_video ]

		INSTANT_RUNNER_START_BUTTON.click(start, outputs = start_outputs)
		INSTANT_RUNNER_START_BUTTON.click(run, outputs = run_outputs)
		INSTANT_RUNNER_STOP_BUTTON.click(stop, outputs = run_outputs)
		INSTANT_RUNNER_CLEAR_BUTTON.click(clear, outputs = [ output_image, output_video ])
		if INSTANT_RUNNER_MIDDLE_START_BUTTON and INSTANT_RUNNER_MIDDLE_STOP_BUTTON and INSTANT_RUNNER_MIDDLE_CLEAR_BUTTON:
			INSTANT_RUNNER_MIDDLE_START_BUTTON.click(start, outputs = start_outputs)
			INSTANT_RUNNER_MIDDLE_START_BUTTON.click(run, outputs = run_outputs)
			INSTANT_RUNNER_MIDDLE_STOP_BUTTON.click(stop, outputs = run_outputs)
			INSTANT_RUNNER_MIDDLE_CLEAR_BUTTON.click(clear, outputs = [ output_image, output_video ])
	if ui_workflow_dropdown:
		ui_workflow_dropdown.change(remote_update, inputs = ui_workflow_dropdown, outputs = [ INSTANT_RUNNER_WRAPPER, INSTANT_RUNNER_MIDDLE_WRAPPER ])


def remote_update(ui_workflow : UiWorkflow) -> Tuple[gradio.Row, gradio.Row]:
	is_instant_runner = ui_workflow == 'instant_runner'

	return gradio.Row(visible = is_instant_runner), gradio.Row(visible = is_instant_runner)


def start() -> Tuple[gradio.Button, gradio.Button, gradio.Button, gradio.Button]:
	while not process_manager.is_processing():
		sleep(0.5)
	return gradio.Button(visible = False), gradio.Button(visible = True), gradio.Button(visible = False), gradio.Button(visible = True)


def run() -> Tuple[gradio.Button, gradio.Button, gradio.Button, gradio.Button, gradio.Image, gradio.Video]:
	step_args = collect_step_args()
	output_path = step_args.get('output_path')
	hardcoded_output_path = suggest_hardcoded_output_path(output_path)

	if hardcoded_output_path:
		step_args['output_path'] = hardcoded_output_path
	if job_manager.init_jobs(state_manager.get_item('jobs_path')):
		create_and_run_job(step_args)
		state_manager.set_item('output_path', output_path)
	if is_image(step_args.get('output_path')):
		return gradio.Button(visible = True), gradio.Button(visible = False), gradio.Button(visible = True), gradio.Button(visible = False), gradio.Image(value = step_args.get('output_path'), visible = True), gradio.Video(value = None, visible = False)
	if is_video(step_args.get('output_path')):
		return gradio.Button(visible = True), gradio.Button(visible = False), gradio.Button(visible = True), gradio.Button(visible = False), gradio.Image(value = None, visible = False), gradio.Video(value = step_args.get('output_path'), visible = True)
	return gradio.Button(visible = True), gradio.Button(visible = False), gradio.Button(visible = True), gradio.Button(visible = False), gradio.Image(value = None), gradio.Video(value = None)


def suggest_hardcoded_output_path(output_path : str) -> Optional[str]:
	target_path = state_manager.get_item('target_path')
	source_paths = state_manager.get_item('source_paths')
	target_name = get_file_name(target_path) or 'target'
	target_extension = get_file_extension(target_path) or ''
	source_name = get_file_name(get_first(source_paths)) or 'source'

	if is_directory(output_path):
		output_directory_path = output_path
	else:
		output_directory_path = os.path.dirname(output_path)

	if not is_directory(output_directory_path):
		return None

	index = 0

	while True:
		file_name = source_name + '-' + target_name + target_extension
		next_output_path = os.path.join(output_directory_path, file_name)

		if not is_file(next_output_path):
			return next_output_path
		index += 1


def create_and_run_job(step_args : Args) -> bool:
	job_id = job_helper.suggest_job_id('ui')

	for key in job_store.get_job_keys():
		state_manager.sync_item(key) #type:ignore[arg-type]

	return job_manager.create_job(job_id) and job_manager.add_step(job_id, step_args) and job_manager.submit_job(job_id) and job_runner.run_job(job_id, process_step)


def stop() -> Tuple[gradio.Button, gradio.Button, gradio.Button, gradio.Button, gradio.Image, gradio.Video]:
	process_manager.stop()
	return gradio.Button(visible = True), gradio.Button(visible = False), gradio.Button(visible = True), gradio.Button(visible = False), gradio.Image(value = None), gradio.Video(value = None)


def clear() -> Tuple[gradio.Image, gradio.Video]:
	while process_manager.is_processing():
		sleep(0.5)
	if state_manager.get_item('target_path'):
		clear_temp_directory(state_manager.get_item('target_path'))
	return gradio.Image(value = None), gradio.Video(value = None)
