#!/usr/bin/python
'''
The client side need to maintain two databases which are unread and readed
and I just use dictionary to store the posts in the fixed format respectively.
unread format: { exupery_page1: [username > line_num > content > serial, ...], ...}
readed format: { exupery_page1: [username > line_num > content > serial, ...], ...}
	Pull:
		display exupery 1:
		    First send the request to server, the server will reply not 
			only with content but also all the posts which specified py 
			this page.And then check whether these posts are already in
			unread and readed,if not match add the posts in the unread.
			Then check whether the content can match with posts specified 
			by this page, if match mark n.And then check in readed, if 
			match mark m in same way.

		post_to_forum 1 hello:
			First send the request and the content in a fixed format to 
			server,the server will stored it in the post_dict

		read_post 1:
			First find the specified posts in the unead,print out them in 
			a fixed format.Meanwhile,the unread should reduce these records
			the readed should add these records.

	Push: when use the push mode,the client should send select a idle port along 
		  with local database(unread, readed) to the server.And then start a new 
		  thread to listen this port to receive the new posts which server sended,
		  Then check them with the unread and readed then add these posts in to unread.
		  Meanwhile, if the posts can match with the current page which the client is
		  reading,print 'There are new posts...'

'''

import sys
import time
import threading
import os
from socket import *

# Send display request to server
def display_confirm(socket, get_command, material_path):
	global username
	socket.sendall(get_command + ' ' + material_path + ' ' + username)

	return True

# Receive the reply from server
def display_receive(socket):
	global unread
	global readed

	reply = socket.recv(1024)
	book_content, current_page, post_content = reply.split('~')

	if post_content != 'null':
		post_content_arr = post_content.split('\n')

		if current_page not in unread.keys() and current_page not in readed.keys():
			for i in range(len(post_content_arr) - 1):
				add_record(unread, current_page, post_content_arr[i])

		elif current_page in unread.keys() and current_page not in readed.keys():
			for i in range(len(post_content_arr) - 1):
				if post_content_arr[i] not in unread[current_page]:
					add_record(unread, current_page, post_content_arr[i])

		elif current_page in unread.keys() and current_page in readed.keys():
			for i in range(len(post_content_arr) - 1):
				if post_content_arr[i] not in unread[current_page] and \
					post_content_arr[i] not in readed[current_page]:
					add_record(unread, current_page, post_content_arr[i])

	# locate n
	n_content = locate_n(book_content, current_page)

	# locate m
	m_n_content = locate_m(n_content, current_page)

	print m_n_content

# Locate n by using the page and line number
def locate_n(book_content, current_page):
	global unread

	n_content = ''
	book_content_arr = book_content.split('\n')

	if current_page in unread.keys():
		# current_page_post = ['...> ...> \n', ...]
		current_page_post = unread[current_page]
		for i in range(len(book_content_arr)):
			n_flag = False
			for j in range(len(current_page_post)):
				if book_content_arr[i].startswith('   ' + current_page_post[j].split(' > ')[1]):
					n_flag = True

			if n_flag:
				n_content += 'n  ' + book_content_arr[i].lstrip() + '\n'
			else:
				n_content += book_content_arr[i] + '\n'
	else:
		n_content += book_content

	return n_content

# Locate m same as locate n
def locate_m(n_content, current_page):
	global readed
	m_content = ''
	n_content_arr = n_content.split('\n')

	if current_page in readed.keys():
		current_page_post = readed[current_page]
		for i in range(len(n_content_arr)):
			m_flag = False
			for j in range(len(current_page_post)):
				if n_content_arr[i].startswith('   ' + current_page_post[j].split(' > ')[1]):
					m_flag = True
			if m_flag:
				m_content += 'm  ' + n_content_arr[i].lstrip() + '\n'
			else:
				m_content += n_content_arr[i] + '\n'

	else:
		m_content += n_content

	return m_content

# Post the content to server in the fixed format
def post_to_forum(socket, username, page, content):
	# page: exupery 1
	format_content = 'post_to_forum' + ' ' + username + ' ' + page + ' ' + \
						content
	socket.sendall(format_content);


def read_post(book_page, line_num):
	## first read from unread, unread --, readed ++
	global readed
	global unread
	# current_page: exuery 1
	book, page = book_page.split()
	current_page = book + '_page' + page

	if current_page in unread.keys():
		current_page_unread_backup = {}
		for key in unread.keys():
			for value in unread[key]:
				add_record(current_page_unread_backup, key, value)

		current_page_unread_line = []

		current_page_unread_bak = current_page_unread_backup[current_page]

		for i in range(len(current_page_unread_bak)):
			num = current_page_unread_bak[i].split(' > ')[1]
			if num == line_num:
				unread[current_page].remove(current_page_unread_bak[i])
				add_record(readed, current_page, current_page_unread_bak[i])

		readed_content = ''
		readed_post = readed[current_page]

		print 'Book by ' + book + ', Page ' + page + ', Line number: ' + line_num

		for i in range(len(readed_post)):
			if readed_post[i].split(' > ')[1] == line_num:
				readed_post_arr = readed_post[i].split(' > ')
				readed_content += readed_post_arr[-1] + ' ' + readed_post_arr[0] + ': ' + readed_post_arr[2] + '\n'

		print readed_content

# Add the post record in local database
def add_record(local_database, page_line, content):
	local_database.setdefault(page_line, []).append(content)

# When the cutdown time expire, request the server, and the server would send
# send the posts associated with the current page.
# And then check whether these posts in unread and readed,and determine whether
# is there new post
def refresh(socket, get_command, material_path):
	global unread
	global readed
	global username

	if display_confirm(socket, get_command, material_path):
		reply = socket.recv(1024)
		book_content, current_page, post_content = reply.split('~')

		if post_content != 'null':
			if current_page in unread.keys() and current_page in readed.keys():
				unread_post_records = unread[current_page]
				readed_post_records = readed[current_page]
				post_content_arr = post_content.split('\n')

				for i in range(len(post_content_arr) - 1):
					if post_content_arr[i] not in unread_post_records and \
						post_content_arr[i] not in readed_post_records:
						return True
				return False

			elif current_page in unread.keys() and current_page not in readed.keys():
				unread_post_records = unread[current_page]
				post_content_arr = post_content.split('\n')

				for i in range(len(post_content_arr) - 1):
					if post_content_arr[i] not in unread_post_records:
						return True
				return False

			elif current_page not in unread.keys() and current_page in readed.keys():
				return False

			else:
				return True
		else:

			return False


# Set the polling_interval,when the time expire call refresh
def cutdown_timer(socket, current_page_record):
	global flag
	global polling_interval
	global current_page
	start = time.time()

	while 1:
		if flag:
			if(time.time() - start >= int(polling_interval)):

				material_path = current_page.replace(' ', '_page')

				if refresh(socket, 'display', material_path):
					print 'There are new posts...'
				start = time.time()
		else:
			flag = True
			start = time.time()


# Send the push mode along with the port and local databases
def send_mode(socket, mode, addr, port, username):
	global unread
	global readed

	push_record = mode + '~' + addr + '~' + str(port) + '~' + str(unread.items()) + '~' + str(readed.items()) + '~' + username
	socket.send(push_record)

# Check whether the reply_post_content along with reply_current page 
# in the local databases, and write some of them in unread
def push_update_unread(reply_current_page, reply_post_content):
	global unread
	global readed
	global m_path
	current_page = m_path

	# write in unread database
	if reply_current_page == current_page:
		add_record(unread, reply_current_page, reply_post_content)
		return True

	# write in unread database
	if current_page == '':
		add_record(unread, reply_current_page, reply_post_content)
		return False


	else:
		# write in unread database
		if reply_current_page not in unread.keys() and reply_current_page not in readed.keys():
			add_record(unread, reply_current_page, reply_post_content)
			return False

		elif reply_current_page in unread.keys():
			if reply_current_page in readed.keys():
				if reply_post_content not in unread[reply_current_page] and reply_post_content not in readed[reply_current_page]:
					add_record(unread, reply_current_page, reply_post_content)
					return False

			else:
				add_record(unread, reply_current_page, reply_post_content)
				return False

		elif reply_current_page not in unread.keys() and reply_current_page in readed.keys():
			if reply_post_content not in readed[reply_current_page]:
				add_record(unread, reply_current_page, reply_post_content)
				return False

		return False


# Display in the push mode, the server only need to send the book_content
def push_display(socket, command, material_path):
	global unread
	global readed

	socket.send('push' + ' ' + command + ' ' + material_path)
	book_content = socket.recv(1024)

	n_content = locate_n(book_content, material_path)
	m_n_content = locate_m(n_content, material_path)

	print m_n_content

# Recv post record from server in push
# and judge whether it's new post
def push_recv(socket, material_path):

	init_flag = False
	while 1:
		reply = socket.recv(1024)
		if reply != '':
			reply_records = reply.split('\n')

			for reply_record in reply_records:
				if reply_record != '':
					reply_record_arr = reply_record.split('~')
					reply_current_page = reply_record_arr[0]
					reply_post_content = reply_record_arr[1]
					if push_update_unread(reply_current_page, reply_post_content) and init_flag:
						print 'There are new Posts...'

			init_flag = True

def main():

	global flag
	tag = True

	global polling_interval
	global username
	global current_page
	mode = sys.argv[1]
	polling_interval = sys.argv[2]
	username = sys.argv[3]

	if mode == 'pull':
		history_reading_page = []

		while True:
			if(len(history_reading_page) == 0):
				current_page = ''
			else:
				current_page = history_reading_page[-1]
			client_command = raw_input('Please input command:')

			if not client_command:
				continue

			elif client_command.startswith('display'):
				get_command, book, page = client_command.split()
				material_path = book + '_page' + page
				current_page_record = book + ' ' + page

				if get_command == 'display':

					if display_confirm(clientSocket, get_command, material_path):
						display_receive(clientSocket)
						history_reading_page.append(current_page_record)
						current_page = history_reading_page[-1]

						if tag:
							thread = threading.Thread(target = cutdown_timer, args = (clientSocket,current_page_record))
							thread.setDaemon(True)
							thread.start()
							tag = False
						flag = False

			elif client_command.startswith('post_to_forum'):
				content = client_command[14:]
				post_to_forum(clientSocket, username, current_page, content)

			elif client_command.startswith('read_post'):
				command, line_num = client_command.split()
				read_post(current_page, line_num)

	elif mode == 'push':
		global unread
		global readed
		global ip
		global m_path

		push_socket = socket(AF_INET, SOCK_STREAM)
		push_socket.bind(('', 0))
		push_socket.listen(10)

		new_port = push_socket.getsockname()[1]


		send_mode(clientSocket, mode, ip, new_port, username)
		connectionSocket, addr = push_socket.accept();
		history_reading_page = []

		thread = threading.Thread(target = push_recv, args = (connectionSocket, m_path))
		thread.setDaemon(True)
		thread.start()

		while True:

			if(len(history_reading_page) == 0):
				current_page = ''
			else:
				current_page = history_reading_page[-1]
			client_command = raw_input('Please input command:')

			if not client_command:
				continue

			elif client_command.startswith('display'):
				get_command, book, page = client_command.split()
				m_path = book + '_page' + page
				current_page_record = book + ' ' + page

				if get_command == 'display':
					history_reading_page.append(current_page_record)
					push_display(clientSocket, get_command, m_path)

			elif client_command.startswith('post_to_forum'):
				content = client_command[14:]
				post_to_forum(clientSocket, username, current_page, content)

			elif client_command.startswith('read_post'):
				command, line_num = client_command.split()
				read_post(current_page, line_num)

if __name__ == '__main__':

	flag = True
	ip = sys.argv[4]
	unread = {}
	readed = {}
	port = int(sys.argv[5])
	clientSocket = socket(AF_INET, SOCK_STREAM)
	clientSocket.connect((ip, port))
	m_path = ''
	main()




